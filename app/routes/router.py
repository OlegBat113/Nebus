from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.organization import Organization
from app.models.building import Building
from app.models.activity import Activity
from app.models.organization_activity import OrganizationActivity
from app.models.building_organization import BuildingOrganization
from app.schemas.schemas import OrganizationSchema
from sqlalchemy import func, text

router = APIRouter()

def load_env(env_path='.env'):
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

# Загрузка переменных окружения
config = load_env()

# В дальнейшем, необходимо заменить на ваш статический API ключ в файле ".env"
API_KEY = config['API_KEY']  

# Проверка API ключа
def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Возвращает организации по ID здания
@router.get("/organizations/building/{building_id}", response_model=List[OrganizationSchema])
def get_organizations_by_building(building_id: int, api_key: str, db: Session = Depends(get_db)):
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение организаций по ID здания
    s = f"""
            SELECT b.*, c.address as building_address
            FROM building_organization a 
            LEFT JOIN organizations b ON b.id = a.organization_id 
            LEFT JOIN buildings c ON c.id = a.building_id
            WHERE a.building_id = {building_id} 
            ORDER BY b.name
        """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)

    organizations = result.fetchall()  # Получаем все результаты
    return organizations


# Возвращает организации по ID деятельности
@router.get("/organizations/activity/{activity_id}", response_model=List[OrganizationSchema])
def get_organizations_by_activity(activity_id: int, api_key: str, db: Session = Depends(get_db)):
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение организаций по ID деятельности
    s = f"""
            SELECT b.*, c.name as activity_name
            FROM organization_activity a
            LEFT JOIN organizations b ON (a.organization_id = b.id)
            LEFT JOIN activities c ON (a.activity_id = c.id)
            WHERE a.activity_id = {activity_id}
            ORDER BY b.name
        """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    organizations = result.fetchall()  # Получаем все результаты
    return organizations

# Возвращает организации по координатам и радиусу
@router.get("/organizations/nearby", response_model=List[OrganizationSchema])
def get_organizations_nearby(latitude: float, longitude: float, radius: float, api_key: str, db: Session = Depends(get_db)):
    verify_api_key(api_key)
    organizations = db.query(Organization).filter(
        func.sqrt(func.pow(Organization.latitude - latitude, 2) + func.pow(Organization.longitude - longitude, 2)) <= radius
    ).all()
    return organizations

# Возвращает организацию по ID
@router.get("/organizations/{organization_id}", response_model=OrganizationSchema)
def get_organization_by_id(organization_id: int, api_key: str, db: Session = Depends(get_db)):
    verify_api_key(api_key)
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

# Возвращает организации по названию деятельности
@router.get("/organizations/search", response_model=List[OrganizationSchema])
def search_organizations_by_activity(activity_name: str, api_key: str, db: Session = Depends(get_db)):
    verify_api_key(api_key)
    activities = db.query(Activity).filter(Activity.name.ilike(f"%{activity_name}%")).all()
    organization_ids = [org.id for act in activities for org in act.organizations]
    organizations = db.query(Organization).filter(Organization.id.in_(organization_ids)).all()
    return organizations

# Возвращает организации по названию
@router.get("/organizations/search_by_name", response_model=List[OrganizationSchema])
def search_organizations_by_name(name: str, api_key: str, db: Session = Depends(get_db)):
    verify_api_key(api_key)
    organizations = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    return organizations

