from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Kamera as KameraModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 5, 'resolusi': 4, 'iso': 3, 'titik_fokus': 3, 'kelas': 4}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(KameraModel.id, KameraModel.harga, KameraModel.resolusi, KameraModel.iso, KameraModel.titik_fokus, KameraModel.kelas)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': kamera.id, 'harga': kamera.harga, 'resolusi': kamera.resolusi, 'iso': kamera.iso, 'titik_fokus': kamera.titik_fokus, 'kelas': kamera.kelas} for kamera in result]

    @property
    def normalized_data(self):
        harga_values = []
        resolusi_values = []
        iso_values = []
        titik_fokus_values = []
        kelas_values = []

        for data in self.data:
            harga_values.append(data['harga'])
            resolusi_values.append(data['resolusi'])
            iso_values.append(data['iso'])
            titik_fokus_values.append(data['titik_fokus'])
            kelas_values.append(data['kelas'])

        return [
            {'id': data['id'],
             'harga': min(harga_values) / data['harga'],
             'resolusi': data['resolusi'] / max(resolusi_values),
             'iso': data['iso'] / max(iso_values),
             'titik_fokus': data['titik_fokus'] / max(titik_fokus_values),
             'kelas': data['kelas'] / max(kelas_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['harga'] ** self.raw_weight['harga'] *
                row['resolusi'] ** self.raw_weight['resolusi'] *
                row['iso'] ** self.raw_weight['iso'] *
                row['titik_fokus'] ** self.raw_weight['titik_fokus'] *
                row['kelas'] ** self.raw_weight['kelas']
            )

            produk.append({
                'id': row['id'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'id': product['id'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id']:
                  round(row['harga'] * weight['harga'] +
                        row['resolusi'] * weight['resolusi'] +
                        row['iso'] * weight['iso'] +
                        row['titik_fokus'] * weight['titik_fokus'] +
                        row['kelas'] * weight['kelas'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class Kamera(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(KameraModel)
        data = [{'id': kamera.id, 'harga': kamera.harga, 'resolusi': kamera.resolusi, 'iso': kamera.iso, 'titik_fokus': kamera.titik_fokus, 'kelas': kamera.kelas} for kamera in session.scalars(query)]
        return self.get_paginated_result('kamera/', data, request.args), HTTPStatus.OK.value


api.add_resource(Kamera, '/kamera')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
