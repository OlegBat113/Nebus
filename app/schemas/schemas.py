from pydantic import BaseModel
from typing import Optional, List


# Схема для зданий -----------------------------------------------
class BuildingSchema(BaseModel):
    id: int
    address: str
    latitude: str
    longitude: str
    class Config:
        orm_mode = True


# Схема для деятельности -----------------------------------------------
class ActivitySchema(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    class Config:
        orm_mode = True


# Схема для телефонов -----------------------------------------------
class PhonesSchema(BaseModel):
    organization_id: int
    phone_number: Optional[List[str]] = None
    class Config:
        orm_mode = True


# Схема для организаций -----------------------------------------------
class OrganizationSchema(BaseModel):
    id: int
    name: str
    address: str
    phone_numbers: Optional[List[str]] = None
    activity: Optional[List[str]] = None
    class Config:
        orm_mode = True



# Если у вас есть другие схемы, добавьте их здесь
