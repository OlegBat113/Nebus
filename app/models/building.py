from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from ..database.database import Base

class Building(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Связь с кросс-таблицей BuildingOrganization
    building_organizations = relationship("BuildingOrganization", back_populates="building")  # Связь с BuildingOrganization

    def __repr__(self):
        return f"<Building(address={self.address}, latitude={self.latitude}, longitude={self.longitude})>" 