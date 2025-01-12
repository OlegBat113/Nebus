from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.models.organization import Organization
from app.models.building import Building
from app.models.activity import Activity
from app.models.organization_activity import OrganizationActivity
from app.models.building_organization import BuildingOrganization
from app.models.phones import Phones
from app.schemas.schemas import OrganizationSchema, ActivitySchema, PhonesSchema, BuildingSchema
from sqlalchemy import func, text
from sqlalchemy.orm import Session

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


# Возвращает список всех зданий из БД -----------------------------------
def get_all_buildings() -> List[BuildingSchema]:
    print(f"-> get_all_buildings: ...")
    s = f"""
        SELECT id, address, latitude, longitude
        FROM buildings
        order by address
    """
    query = text(s)
    print(f"query: {query}")
    db = get_db()
    result = db.execute(query)
    recs = result.fetchall()
    # Список всех зданий
    buildings = []
    for rec in recs:
        #print(f"rec: {rec}")
        # Создание объекта BuildingSchema
        building = BuildingSchema(id=rec.id, address=rec.address, latitude=rec.latitude, longitude=rec.longitude)
        buildings.append(building)
    return buildings


# Возвращает список телефонов организации -----------------------------------
def get_phones(organization_id: int, db: Session = Depends(get_db)) -> List[PhonesSchema]:
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
        phone = PhonesSchema(
            organization_id=organization_id, 
            phone_number=rec.phone_number
        )
        phones.append(phone)
    print(f"phones: {phones}")
    return phones


# Возвращает адрес по  id организации -----------------------------------
def get_building_by_organization_id(organization_id: int, db: Session = Depends(get_db)) -> BuildingSchema:
    print(f"-> get_building_by_organization_id: organization_id={organization_id} ...")
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
    building = BuildingSchema(
        id=rec[0], 
        address=rec[1], 
        latitude=rec[2], 
        longitude=rec[3]
    )
    print(f"BuildingSchema: {building}")
    return building


# Возвращает список деятельностей организации -----------------------------------
def get_activities(organization_id: Optional[int] = None) -> List[ActivitySchema]:
    print(f"-> get_activities: organization_id={organization_id} ...")
    s = f"""
        SELECT c.id, c.name, c.parent_id, c.level
        FROM organization_activity a 
        LEFT JOIN activities c ON (a.activity_id = c.id)
    """
    if organization_id is not None:
        s += f" WHERE a.organization_id = {organization_id}"
    s += f" ORDER BY c.level, c.parent_id"
    query = text(s)
    print(f"query: {query}")
    db = get_db()
    result = db.execute(query)
    recs = result.fetchall()
    #print(f"recs: {recs}")
    activities = []
    for rec in recs:
        #print(f"rec: {rec}")
        activity = ActivitySchema(id=rec.id, name=rec.name, parent_id=rec.parent_id, level=rec.level)
        #print(f"activity: {activity}")
        activities.append(activity)
    return activities


# Возвращает деятельность по ID -----------------------------------
def get_activity(activity_id: int, db: Session) -> Optional[ActivitySchema]:
    """Возвращает деятельность по ID."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        return None
    return activity 


# =======================================================================================
# Главная страница -----------------------------------
@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    print(f"-> Главная страница: ...")
    db: Session = get_db()
    # Список всех зданий
    buildings = get_all_buildings()
    activities = get_activities()
    buildings_list = []
    activities_list = []
    for building in buildings:
        #print(f"building: {building}")
        buildings_list.append({"id": building.id, "address": building.address})
    for activity in activities:
        #print(f"activity: {activity}")
        activities_list.append({
            "id": activity.id, 
            "name": activity.name, 
            "parent_id": activity.parent_id, 
            "level": activity.level
        })
    data = {"api_key": API_KEY, 
            "request": request, 
            "buildings": buildings_list, 
            "activities": activities_list
            }
    return templates.TemplateResponse("index.html", data)


# Информация -----------------------------------
@router.get("/info", response_class=HTMLResponse)
def read_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


# Возвращает список организаций по ID здания -----------------------------------
@router.post("/organizations/building", response_class=HTMLResponse)
def get_organizations_by_building(
    building_id: int = Form(...),
    api_key: str = Form(...),  # API ключ
    db: Session = Depends(get_db)
) -> HTMLResponse:
    print(f"-> (POST) get_organizations_by_building: building_id={building_id} ...")

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

    # Формирование таблицы в HTML формате
    sTable = """
        <table class="table">
            <thead class="thead-light">
                <tr>
                    <th scope="col">ID</th>
                    <th scope="col">Название</th>
                    <th scope="col">Адрес</th>
                    <th scope="col">Телефоны</th>
                    <th scope="col">Деятельности</th>
                </tr>
            </thead>
            <tbody>
    """
    # Цикл по всей выборке
    for org_rec in recs:
        print(f"org_rec: {org_rec}")

        # Получение телефонов организации
        phones = get_phones(org_rec.id, db)
        phones_list = ""
        for phone in phones:
            print(f"phone: {phone}")
            phones_list += f"{phone.phone_number}<br>"
        print(f"phones_list: {phones_list}")

        # Получение деятельностей организации
        activities = get_activities(organization_id = org_rec.id)
        print(f"ActivitiesSchema: {activities}")
        # Список всех деятельностей организации
        activities_names = ""
        # Цикл по всем деятельностям
        for activity in activities:
            print(f"activity: {activity}")
            activities_names += f"[{activity.level}] {activity.name}<br>"

        # Получение адреса организации
        building = get_building_by_organization_id(org_rec.id, db)
        print(f"BuildingSchema: {building}")

        # Формирование строки таблицы
        sRow = f"""
            <tr>
                <td scope="row">{org_rec.id}</td>
                <td>{org_rec.name}</td>
                <td>{building.address}</td>
                <td>{phones_list}</td>
                <td>{activities_names}</td>
            </tr>
        """
        sTable += sRow

    # Закрытие таблицы
    sTable += """
            </tbody>
        </table>
    """
    # Возвращаем таблицу в HTML формате
    return HTMLResponse(content=sTable)


# Добавление новой деятельности -----------------------------------
@router.post("/add_activity/", response_model=ActivitySchema)
def add_activity(
    parent_id: int = Form(...),
    name: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
) -> ActivitySchema:
    """Добавление новой деятельности с проверкой уровня вложенности."""
    print(f"-> (POST) add_activity: parent_id={parent_id}, name={name} ...")

    # Проверка API ключа
    verify_api_key(api_key)

    # Проверка уровня родителя деятельности
    if parent_id is not None:
        activity = get_activity(parent_id, db)
        if (activity is not None) and (activity.level >= 3):
            raise HTTPException(status_code=400, detail="ERROR: Уровень вложенности родителя деятельности не должен превышать 3!")

    # Добавление новой деятельности
    new_activity = Activity(name=name, parent_id=parent_id)
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


# Возвращает список организаций по ID деятельности -----------------------------------
@router.post("/organizations/activity", response_class=HTMLResponse)
def get_organizations_by_activity(
    activity_id: int = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    print(f"-> (POST) get_organizations_by_activity: activity_id={activity_id} ...")
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

    # Формирование таблицы в HTML формате
    sTable = """
        <table class="table">
            <thead class="thead-light">
                <tr>
                    <th scope="col">ID</th>
                    <th scope="col">Название</th>
                    <th scope="col">Адрес</th>
                    <th scope="col">Телефоны</th>
                    <th scope="col">Деятельности</th>
                </tr>
            </thead>
            <tbody>
    """    
    # Цикл по всей выборке
    for org_rec in recs:
        print(f"org_rec: {org_rec}")

        phoneSchemas = get_phones(org_rec.id, db)
        #print(f"phoneSchemas: {phoneSchemas}")
        phones_list = ""
        for phone in phoneSchemas:
            phones_list += f"{phone.phone_number}<br>"

        activitySchemas = get_activities(organization_id = org_rec.id)
        print(f"activitySchemas: {activitySchemas}")    
        activities_list = ""
        for activity in activitySchemas:
            activities_list += f"[{activity.level}] {activity.name}<br>"

        building = get_building_by_organization_id(org_rec.id, db)
        print(f"BuildingSchema: {building}")

        sRow = f"""
            <tr>
                <td scope="row">{org_rec.id}</td>
                <td>{org_rec.name}</td>
                <td>{building.address}</td>
                <td>{phones_list}</td>
                <td>{activities_list}</td>
            </tr>
        """
        sTable += sRow

    # Закрытие таблицы
    sTable += """
            </tbody>
        </table>
    """
    # Возвращаем таблицу в HTML формате
    return HTMLResponse(content=sTable)


# Возвращает список организаций по координатам и радиусу -----------------------------------
@router.post("/organizations/nearby", response_class=HTMLResponse)
def get_organizations_nearby(
    latitude: float = Form(...), 
    longitude: float = Form(...), 
    radius: float = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    print(f"-> (POST) get_organizations_nearby: latitude={latitude}, longitude={longitude}, radius={radius}, api_key={api_key} ...")
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

        activities = get_activities(organization_id = org_rec.id)
        print(f"ActivitiesSchema: {activities}")    
        activities_names = []
        for activity in activities:
            activities_names.append(activity.name)

        building = get_building_by_organization_id(org_rec.id, db)
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

