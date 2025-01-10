from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    phone_numbers = Column(String, nullable=True)  # Хранение номеров телефонов в виде строки
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)  # Внешний ключ на Building

    building = relationship("Building")
    organization_activities = relationship("OrganizationActivity", back_populates="organization")  # Связь с OrganizationActivity
    building_organizations = relationship("BuildingOrganization", back_populates="organization")  # Связь с BuildingOrganization

    def __repr__(self):
        return f"<Organization(name={self.name}, phone_numbers={self.phone_numbers})>" 