from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('activities.id'), nullable=True)

    parent = relationship('Activity', back_populates='children', remote_side=[id])
    children = relationship('Activity', back_populates='parent')
    organization_activities = relationship("OrganizationActivity", back_populates="activity")  # Связь с OrganizationActivity

    def __repr__(self):
        return f"<Activity(name={self.name}, parent_id={self.parent_id})>"

    # Возвращает уровень вложенности деятельности.
    def get_level(self):
        """Возвращает уровень вложенности деятельности."""
        level = 1
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level

    # Проверяет, можно ли добавить новую деятельность к родительской.
    @classmethod
    def can_add_activity(cls, parent_activity):
        """Проверяет, можно ли добавить новую деятельность к родительской."""
        if parent_activity.get_level() < 3:  # Уровень вложенности не должен превышать 3
            return True
        return False 