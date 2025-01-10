from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class BuildingOrganization(Base):
    __tablename__ = 'building_organization'

    building_id = Column(Integer, ForeignKey('buildings.id', name='fk_building_id'), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', name='fk_organization_id'), primary_key=True)

    building = relationship("Building", back_populates="building_organizations")
    organization = relationship("Organization", back_populates="building_organizations") 