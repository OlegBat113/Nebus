from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class OrganizationActivity(Base):
    __tablename__ = 'organization_activity'

    organization_id = Column(Integer, ForeignKey('organizations.id', name='fk_organization_id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id', name='fk_activity_id'), primary_key=True)

    organization = relationship("Organization", back_populates="organization_activities")
    activity = relationship("Activity", back_populates="organization_activities") 