from pydantic import BaseModel
from typing import Optional, List

class OrganizationSchema(BaseModel):
    id: int
    name: str
    phone_numbers: Optional[str] = None

    #class Config:
    #    orm_mode = True

# Если у вас есть другие схемы, добавьте их здесь

