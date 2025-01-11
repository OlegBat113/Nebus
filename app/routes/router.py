from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.organization import Organization
from app.models.building import Building
from app.models.activity import Activity
from app.models.organization_activity import OrganizationActivity
from app.models.building_organization import BuildingOrganization
from app.models.phones import Phones
from app.schemas.schemas import OrganizationSchema, BuildingSchema, ActivitySchema
from sqlalchemy import func, text
from databases import Database

# Создание роутера
router = APIRouter()

# Загрузка переменных окружения
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


# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")


# Главная страница -----------------------------------
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Информация -----------------------------------
@router.get("/info", response_class=HTMLResponse)
async def read_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


# Возвращает список телефонов организации -----------------------------------
async def get_phones(organization_id: int, db: Database = Depends(get_db)) -> List[str]:
    query = text("SELECT p.phone_number FROM phones p WHERE p.organization_id = :organization_id")
    result = await db.fetch_all(query, values={"organization_id": organization_id})
    return [rec.phone_number for rec in result]


# Возвращает список деятельностей организации -----------------------------------
async def get_activities(organization_id: int, db: Database = Depends(get_db)) -> List[ActivitySchema]:
    query = text("SELECT c.id, c.name, c.parent_id FROM organization_activity a LEFT JOIN activities c ON (a.activity_id = c.id) WHERE a.organization_id = :organization_id")
    result = await db.fetch_all(query, values={"organization_id": organization_id})
    return [ActivitySchema(id=rec.id, name=rec.name, parent_id=rec.parent_id) for rec in result]


# Возвращает адрес по  id организации -----------------------------------
async def get_building(organization_id: int, db: Database = Depends(get_db)) -> BuildingSchema:
    print(f"-> get_building: organization_id={organization_id} ...")
    s = f"""
        SELECT c.id, c.address, c.latitude, c.longitude
        FROM building_organization a
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.organization_id = {organization_id}
    """
    query = text(s)
    print(f"query: {query}")
    result = await db.fetch_one(query)
    if result is None:
        return None

    print(f"rec: {result}")
    print(f"rec[0]: {result[0]}")
    print(f"rec[1]: {result[1]}")
    print(f"rec[2]: {type(result[2])}")
    print(f"rec[3]: {result[3]}")
    building = BuildingSchema(
        id=result[0], 
        address=result[1], 
        latitude=result[2], 
        longitude=result[3]
    )
    print(f"BuildingSchema: {building}")
    return building


# Возвращает список организаций по ID здания -----------------------------------
@router.get("/organizations/building/{building_id}", response_model=List[OrganizationSchema])
async def get_organizations_by_building(building_id: int, api_key: str, db: Database = Depends(get_db)):
    print(f"-> get_organizations_by_building: building_id={building_id} ...")
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение списка организаций по ID здания
    query = text(f"""
        SELECT b.id, b.name, c.address
        FROM building_organization a 
        LEFT JOIN organizations b ON b.id = a.organization_id 
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.building_id = :building_id 
        ORDER BY b.name
    """)
    
    result = await db.fetch_all(query, values={"building_id": building_id})

    # Список всех организаций в здании (тип будет List[OrganizationSchema])
    organizations = []

    # Цикл по всей выборке
    for rec in result:
        print(rec)

        # Получение телефонов организации
        phones = await get_phones(rec.id, db)
        
        # Получение деятельностей организации
        activities = await get_activities(rec.id, db)
        activities_names = []
        for activity in activities:
            print(f"activity: {activity}")
            activities_names.append(activity.name)

        # Создание организации по схеме
        organization = OrganizationSchema(
            id=rec.id, 
            name=rec.name, 
            address=rec.address,
            phone_numbers=phones, 
            activity=activities_names)
        print(f"OrganizationSchema: {organization}")
        # Добавление этой организации в общий список организаций
        organizations.append(organization)
    return organizations


# Возвращает список организаций по ID деятельности -----------------------------------
@router.get("/organizations/activity/{activity_id}", response_model=List[OrganizationSchema])
async def get_organizations_by_activity(activity_id: int, api_key: str, db: Database = Depends(get_db)):
    print(f"-> get_organizations_by_activity: activity_id={activity_id} ...")
    # Проверка API ключа
    verify_api_key(api_key)

    # Список всех организаций по ID деятельности
    organizations = []

    # Получение организаций по ID деятельности
    query = text(f"""
        SELECT b.id, b.name
        FROM organization_activity a
        LEFT JOIN organizations b ON (a.organization_id = b.id)
        WHERE a.activity_id = :activity_id
        ORDER BY b.name
    """)
    result = await db.fetch_all(query, values={"activity_id": activity_id})

    # Цикл по всей выборке
    for org_rec in result:
        print(f"organization_rec: {org_rec}")

        # Получение здание организации
        building = await get_building(org_rec.id, db)
        print(f"BuildingSchema: {building}")
        if building is None:
            sAddress = None
        else:
            sAddress = building.address

        # Получение телефонов организации
        phones = await get_phones(org_rec.id, db)

        # Получение деятельностей организации
        activities = await get_activities(org_rec.id, db)
        activities_names = []
        for activity in activities:
            print(f"ActivitySchema: {activity}")
            activities_names.append(activity.name)

        # Создание организации по схеме
        organization = OrganizationSchema(
            id=org_rec.id, 
            name=org_rec.name, 
            address=sAddress,
            phone_numbers=phones, 
            activity=activities_names)
        print(f"OrganizationSchema: {organization}")

        # Добавление этой организации в общий список организаций
        organizations.append(organization)

    return organizations


# Возвращает список организаций по координатам и радиусу -----------------------------------
@router.get("/organizations/nearby", response_model=List[OrganizationSchema])
async def get_organizations_nearby(latitude: float, longitude: float, radius: float, api_key: str, db: Database = Depends(get_db)):
    print(f"-> get_organizations_nearby: latitude={latitude}, longitude={longitude}, radius={radius} ...")
    verify_api_key(api_key)
    organizations = db.query(Organization).filter(
        func.sqrt(func.pow(Organization.latitude - latitude, 2) + func.pow(Organization.longitude - longitude, 2)) <= radius
    ).all()
    return organizations


# Возвращает организацию по ID -----------------------------------
@router.get("/organizations/{organization_id}", response_model=OrganizationSchema)
async def get_organization_by_id(organization_id: int, api_key: str, db: Database = Depends(get_db)):
    print(f"-> get_organization_by_id: organization_id={organization_id} ...")
    verify_api_key(api_key)
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


# Возвращает организации по названию деятельности -----------------------------------
@router.get("/organizations/search", response_model=List[OrganizationSchema])
async def search_organizations_by_activity(activity_name: str, api_key: str, db: Database = Depends(get_db)):
    verify_api_key(api_key)
    activities = db.query(Activity).filter(Activity.name.ilike(f"%{activity_name}%")).all()
    organization_ids = [org.id for act in activities for org in act.organizations]
    organizations = db.query(Organization).filter(Organization.id.in_(organization_ids)).all()
    return organizations


# Возвращает организации по названию -----------------------------------
@router.get("/organizations/search_by_name", response_model=List[OrganizationSchema])
async def search_organizations_by_name(name: str, api_key: str, db: Database = Depends(get_db)):
    verify_api_key(api_key)
    organizations = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    return organizations

