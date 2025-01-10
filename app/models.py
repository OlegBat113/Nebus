from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# Модель для кросс-таблицы "Организация - Деятельность"
class OrganizationActivity(Base):
    __tablename__ = 'organization_activity'

    organization_id = Column(Integer, ForeignKey('organizations.id', name='fk_organization_id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id', name='fk_activity_id'), primary_key=True)

    organization = relationship("Organization", back_populates="organization_activities")
    activity = relationship("Activity", back_populates="organization_activities")


# Модель для кросс-таблицы "Здание - Организация"
class BuildingOrganization(Base):
    __tablename__ = 'building_organization'

    building_id = Column(Integer, ForeignKey('buildings.id', name='fk_building_id'), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', name='fk_organization_id'), primary_key=True)

    building = relationship("Building", back_populates="building_organizations")
    organization = relationship("Organization", back_populates="building_organizations")


# Модель для таблицы "Деятельность"
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


# Модель для таблицы "Здания"
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


# Модель для таблицы "Организации"
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


