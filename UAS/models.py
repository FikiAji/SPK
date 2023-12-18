from sqlalchemy import Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Kamera(Base):
    __tablename__ = 'kamera'
    id: Mapped[str] = mapped_column(primary_key=True)
    harga: Mapped[int] = mapped_column()
    resolusi: Mapped[int] = mapped_column()
    iso: Mapped[int] = mapped_column()
    titik_fokus: Mapped[int] = mapped_column()
    kelas: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"Kamera(id={self.id!r}, harga={self.harga!r})"
