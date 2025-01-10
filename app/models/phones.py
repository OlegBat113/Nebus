from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class Phones(Base):
    __tablename__ = 'phones'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)  # ключ на Building
    phone_number = Column(String, nullable=True)  # Хранение номеров телефонов в виде строки
    organization = relationship("Organization", back_populates="phones")

    def __repr__(self):
        return f"<Phones(organization_id={self.organization_id}, phone_number={self.phone_number})>" 
