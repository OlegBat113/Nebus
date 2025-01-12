from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(Integer, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('activities.id'), nullable=True)

    parent = relationship('Activity', back_populates='children', remote_side=[id])
    children = relationship('Activity', back_populates='parent')
    organization_activities = relationship("OrganizationActivity", back_populates="activity")  # Связь с OrganizationActivity

    def __repr__(self):
        return f"<Activity(name={self.name}, parent_id={self.parent_id})>"



