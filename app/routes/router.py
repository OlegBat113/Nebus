from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
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
from app.schemas.schemas import OrganizationSchema, ActivitySchema, PhonesSchema, BuildingSchema
from sqlalchemy import func, text

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

# Проверка API ключа
def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Загрузка переменных окружения
config = load_env()

# В дальнейшем, необходимо заменить на ваш статический API ключ в файле ".env"
API_KEY = config['API_KEY']  


# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")

# Главная страница -----------------------------------
@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    print(f"-> Главная страница: ...")
    db: Session = get_db()

    s = f"""
        SELECT id, address
        FROM buildings
        order by address
    """
    query = text(s)
    print(f"query: {query}")
    print(f"db: {type(db)}")
    result = db.execute(query)
    recs = result.fetchall()
    buildings = []
    for rec in recs:
        print(f"building_rec : {rec}")
        buildings.append({"id": rec.id, "address": rec.address})

    return templates.TemplateResponse("index.html", {"request": request, "buildings": buildings})


# Информация -----------------------------------
@router.get("/info", response_class=HTMLResponse)
def read_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


# Возвращает список тестовых организаций -----------------------------------
def get_phones(organization_id: int, db: Session = Depends(get_db)) -> List[str]:
    print(f"-> get_phones: organization_id={organization_id} ...")
    s = f"""
        SELECT p.phone_number
        FROM phones p
        WHERE p.organization_id = {organization_id}
    """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    phones = []
    for rec in recs:
        phones.append(rec.phone_number)
    print(f"phones: {phones}")
    return phones


# Возвращает адрес по  id организации -----------------------------------
def get_building(organization_id: int, db: Session = Depends(get_db)) -> BuildingSchema:
    print(f"-> get_building: organization_id={organization_id} ...")
    s = f"""
        SELECT c.id, c.address, c.latitude, c.longitude
        FROM building_organization a
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.organization_id = {organization_id}
    """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    if len(recs) == 0:
        return None
    rec = recs[0]
    print(f"build_rec: {rec}")
    print(f"build_rec[0]: {rec[0]}")
    print(f"build_rec[1]: {rec[1]}")
    print(f"build_rec[2]: {type(rec[2])}")
    print(f"build_rec[3]: {rec[3]}")
    building = BuildingSchema(
        id=rec[0], 
        address=rec[1], 
        latitude=rec[2], 
        longitude=rec[3]
    )
    print(f"BuildingSchema: {building}")
    return building

# Возвращает список деятельностей организации -----------------------------------
def get_activities(organization_id: int, db: Session = Depends(get_db)) -> List[ActivitySchema]:
    print(f"-> get_activities: organization_id={organization_id} ...")
    s = f"""
        SELECT c.id, c.name, c.parent_id 
        FROM organization_activity a 
        LEFT JOIN activities c ON (a.activity_id = c.id) 
        WHERE a.organization_id = {organization_id}
    """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    print(f"recs: {recs}")
    activities = []
    for rec in recs:
        print(f"rec: {rec}")
        activity = ActivitySchema(id=rec.id, name=rec.name, parent_id=rec.parent_id)
        print(f"activity: {activity}")
        activities.append(activity)
    return activities


# Возвращает список организаций по ID здания -----------------------------------
@router.get("/organizations/building/{building_id}", response_model=List[OrganizationSchema])
def get_organizations_by_building(building_id: int, api_key: str, db: Session = Depends(get_db)):
    print(f"-> get_organizations_by_building: building_id={building_id} ...")
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение списка организаций по ID здания
    s = f"""
        SELECT b.id, b.name, c.address
        FROM building_organization a 
        LEFT JOIN organizations b ON b.id = a.organization_id 
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.building_id = {building_id} 
        ORDER BY b.name
    """
    # Формирование запроса
    query = text(s)
    print(f"query: {query}")

    # Выполнение запроса
    result = db.execute(query)
    recs = result.fetchall()  # Получаем все результаты

    # Список всех организаций в здании (тип будет List[OrganizationSchema])
    organizations = []

    # Цикл по всей выборке
    for org_rec in recs:
        print(f"org_rec: {org_rec}")

        # Получение телефонов организации
        phones_list = get_phones(org_rec.id, db)
        print(f"phones_list: {phones_list}")

        # Получение деятельностей организации
        activities = get_activities(org_rec.id, db)
        print(f"ActivitiesSchema: {activities}")
        # Список всех деятельностей организации
        activities_names = []
        # Цикл по всем деятельностям
        for activity in activities:
            print(f"activity: {activity}")
            activities_names.append(activity.name)

        # Получение адреса организации
        building = get_building(org_rec.id, db)
        print(f"BuildingSchema: {building}")

        # Создание организации по схеме
        organization = OrganizationSchema(
            id=org_rec.id, 
            name=org_rec.name, 
            address=building.address,
            phone_numbers=phones_list, 
            activity=activities_names
        )
        print(f"OrganizationSchema: {organization}")

        # Добавление этой организации в общий список организаций
        organizations.append(organization)
    return organizations


# Возвращает список организаций по ID деятельности -----------------------------------
@router.get("/organizations/activity/{activity_id}", response_model=List[OrganizationSchema])
def get_organizations_by_activity(activity_id: int, api_key: str, db: Session = Depends(get_db)):
    print(f"-> get_organizations_by_activity: activity_id={activity_id} ...")
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение организаций по ID деятельности
    s = f"""
            SELECT b.id, b.name
            FROM organization_activity a
            LEFT JOIN organizations b ON (a.organization_id = b.id)
            WHERE a.activity_id = {activity_id}
            ORDER BY b.name
        """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()  # Получаем все результаты
    organizations = []
    for org_rec in recs:
        print(f"org_rec: {org_rec}")

        phones_list = get_phones(org_rec.id, db)
        print(f"phones_list: {phones_list}")

        activities = get_activities(org_rec.id, db)
        print(f"ActivitiesSchema: {activities}")    
        activities_names = []
        for activity in activities:
            activities_names.append(activity.name)

        building = get_building(org_rec.id, db)
        print(f"BuildingSchema: {building}")

        organization = OrganizationSchema(
            id=org_rec.id, 
            name=org_rec.name, 
            address=building.address,
            phone_numbers=phones_list, 
            activity=activities_names
        )
        print(f"OrganizationSchema: {organization}")
        organizations.append(organization)
    return organizations


# Возвращает список организаций по координатам и радиусу -----------------------------------
@router.post("/organizations/nearby")
def get_organizations_nearby(
    latitude: float = Form(...), 
    longitude: float = Form(...), 
    radius: float = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
):
    print(f"-> get_organizations_nearby: latitude={latitude}, longitude={longitude}, radius={radius}, api_key={api_key} ...")
    verify_api_key(api_key)

    # Получение организаций по ID деятельности
    s = f"""
            SELECT b.id, b.name
            FROM organization_activity a
            LEFT JOIN organizations b ON (a.organization_id = b.id)
            WHERE a.activity_id = 2
            ORDER BY b.name
        """
    query = text(s)
    print(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()  # Получаем все результаты
    organizations = []
    for org_rec in recs:
        print(f"org_rec: {org_rec}")

        phones_list = get_phones(org_rec.id, db)
        print(f"phones_list: {phones_list}")

        activities = get_activities(org_rec.id, db)
        print(f"ActivitiesSchema: {activities}")    
        activities_names = []
        for activity in activities:
            activities_names.append(activity.name)

        building = get_building(org_rec.id, db)
        print(f"BuildingSchema: {building}")

        organization = OrganizationSchema(
            id=org_rec.id, 
            name=org_rec.name, 
            address=building.address,
            phone_numbers=phones_list, 
            activity=activities_names
        )
        print(f"OrganizationSchema: {organization}")
        organizations.append(organization)
    #return organizations
    s = """
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Название</th>
                    <th>Адрес</th>
                    <th>Телефоны</th>
                    <th>Деятельности</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1 колонка</td>
                    <td>2 колонка</td>
                    <td>3 колонка</td>
                    <td>4 колонка</td>
                    <td>5 колонка</td>
                </tr>
            </tbody>
        </table>
    """
    return HTMLResponse(content=s)

# Возвращает организацию по ID -----------------------------------
@router.get("/organizations/{organization_id}", response_model=OrganizationSchema)
def get_organization_by_id(organization_id: int, api_key: str, db: Session = Depends(get_db)):
    print(f"-> get_organization_by_id: organization_id={organization_id} ...")
    verify_api_key(api_key)
    
    #organization = db.query(Organization).filter(Organization.id == organization_id).first()
    #if not organization:
    #    raise HTTPException(status_code=404, detail="Organization not found")
    #return organization
    
    return HTMLResponse(content='<div>return from get_organization_by_id</div>')


# Возвращает организации по названию деятельности -----------------------------------
@router.get("/organizations/search", response_model=List[OrganizationSchema])
def search_organizations_by_activity(activity_name: str, api_key: str, db: Session = Depends(get_db)):
    print(f"-> search_organizations_by_activity: activity_name={activity_name} ...")
    verify_api_key(api_key)
    activities = db.query(Activity).filter(Activity.name.ilike(f"%{activity_name}%")).all()
    organization_ids = [org.id for act in activities for org in act.organizations]
    organizations = db.query(Organization).filter(Organization.id.in_(organization_ids)).all()
    return organizations


# Возвращает организации по названию -----------------------------------
@router.get("/organizations/search_by_name", response_model=List[OrganizationSchema])
def search_organizations_by_name(name: str, api_key: str, db: Session = Depends(get_db)):
    print(f"-> search_organizations_by_name: name={name} ...")
    verify_api_key(api_key)
    organizations = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    return organizations

