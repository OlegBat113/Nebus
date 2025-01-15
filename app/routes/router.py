import logging
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
import math
import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO)  # Установите уровень логирования
#logging.basicConfig(level=logging.DEBUG)  # Установите уровень логирования

# Создание логгера
logger = logging.getLogger(__name__) 

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


# Возвращает список всех зданий из БД -----------------------------------------------------------------------------------------------------------------------
def get_all_buildings(db: Session):
    logger.info(f"get_all_buildings() -> ...")
    logger.debug(f"Запрос на получение всех зданий.")
    s = f"""
        SELECT id, address, latitude, longitude
        FROM buildings
        order by address
    """
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    # Список всех зданий
    buildings = result.fetchall()
    logger.debug(f"buildings: {buildings}")
    logger.debug(f"End get_all_buildings() -> ...")
    return buildings


# Возвращает список телефонов организации -----------------------------------------------------------------------------------------------------------------------
def get_phones(
        db: Session, 
        organization_id: int
):
    logger.info(f"get_phones() -> ...")
    logger.debug(f"Запрос на получение телефонов организации: organization_id={organization_id} ...")
    s = f"""
        SELECT phone_number
        FROM phones
        WHERE organization_id = {organization_id}
    """
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    phones = []
    for rec in recs:
        phone = PhonesSchema(
            organization_id=organization_id, 
            phone_number=rec.phone_number
        )
        phones.append(phone)
    logger.debug(f"phones: {phones}")
    logger.debug(f"End get_phones() -> ...")
    return phones


# Возвращает адрес по  id организации -----------------------------------------------------------------------------------------------------------------------
def get_building_by_organization_id(
        db: Session, 
        organization_id: int
) -> BuildingSchema:
    logger.info(f"get_building_by_organization_id() -> ...")
    logger.debug(f"Запрос на получение адреса организации: organization_id={organization_id} ...")
    s = f"""
        SELECT c.id, c.address, c.latitude, c.longitude
        FROM building_organization a
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.organization_id = {organization_id}
    """
    query = text(s)
    logger.debug(f"query: {query}")
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
    logger.debug(f"BuildingSchema: {building}")
    logger.debug(f"End get_building_by_organization_id() -> ...")
    return building


# Возвращает список деятельностей организации -----------------------------------------------------------------------------------------------------------------------
def get_activities(
        db: Session, 
        organization_id: Optional[int] = None
) -> List[ActivitySchema]:
    logger.info(f"get_activities() -> ...")
    logger.debug(f"Запрос на получение деятельностей организации: organization_id={organization_id} ...")
    if organization_id is not None:
        logger.debug(f"organization_id: {organization_id}")
        s = f"""
            SELECT c.id, c.name, c.parent_id, c.level
            FROM organization_activity a 
            LEFT JOIN activities c ON (a.activity_id = c.id)
            WHERE a.organization_id = {organization_id}
            ORDER BY c.level, c.parent_id
        """
    else:
        s = f"""
            SELECT c.id, c.name, c.parent_id, c.level
            FROM activities c
            ORDER BY c.level, c.parent_id
        """
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    #print(f"activities recs: {recs}")
    activities = []
    for rec in recs:
        #print(f"rec: {rec}")
        activity = ActivitySchema(id=rec.id, name=rec.name, parent_id=rec.parent_id, level=rec.level)
        activities.append(activity)
    logger.debug(f"activities: {activities}")
    logger.debug(f"End get_activities() -> ...")
    return activities


# Возвращает деятельность по ID ---------------------------------------------------------------------------------------------------------------
def get_activity_by_id(
        db: Session, 
        activity_id: int
):
    logger.info(f"get_activity_by_id() -> ...")
    logger.debug(f"Запрос на получение деятельности по ID: activity_id={activity_id} ...")
    """Возвращает деятельность по ID."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        return None
    logger.debug(f"activity: {activity}")
    logger.debug(f"End get_activity_by_id() -> ...")
    return activity 


# расстояние между двумя точками (в метрах) по координатам широты и долготы (в градусах) ----------------------------------------------------
def distance(lat1, lon1, lat2, lon2):
    # параметры
    # lat1, lon1 - координаты первой точки
    # lat2, lon2 - координаты второй точки
    # R - радиус Земли
    # dLat - разница широт
    # dLon - разница долгот
    # a - промежуточная переменная
    # c - промежуточная переменная

    R = 6371000
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
    
    # формула Гаусса
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1 * math.pi / 180.0) * math.cos(lat2 * math.pi / 180.0) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Возвращает список организаций по ID здания --------------------------------------------------------------------------------------------------
def get_organizations_by_building(
        db: Session, 
        building_id: int
):
    logger.info(f"get_organizations_by_building() -> ...")
    logger.debug(f"Запрос на получение организаций по ID здания: building_id={building_id} ...")
    s = f"""
        SELECT b.id, b.name, c.address
        FROM building_organization a 
        LEFT JOIN organizations b ON b.id = a.organization_id 
        LEFT JOIN buildings c ON c.id = a.building_id
        WHERE a.building_id = {building_id} 
        ORDER BY b.name
    """
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    logger.debug(f"recs: {recs}")
    logger.debug(f"End get_organizations_by_building() -> ...")
    return recs


# Возвращает организацию по ID -------------------------------------------------------------------------------------------
def get_organization(
        db: Session, 
        organization_id: int
) -> OrganizationSchema:
    logger.info(f"get_organization() -> ...")
    logger.debug(f"Запрос на получение организации: organization_id={organization_id} ...")
    rec = db.query(Organization).filter(Organization.id == organization_id).first()
    
    building = get_building_by_organization_id(db=db, organization_id=rec.id)   
    organization = OrganizationSchema(id=rec.id, name=rec.name, address=building.address)
    
    logger.debug(f"organization: {organization}")
    logger.debug(f"End get_organization() -> ...")
    return organization


# класс узла дерева Деятельностей ---------------------------------------------------------------------------------------------------------
class TreeNode:
    max_level = 3
    current_id = 0
    # функция инициализации узла
    def __init__(self, id, name, level=0, parent_id=None):
        if id is None:
            self.current_id += 1
            self.id = self.current_id
        else:
            self.id = id
            if id > self.current_id:
                self.current_id = id
        self.name = name
        self.level = level
        self.parent_id = parent_id
        self.childrens = []

    # функция добавления потомка
    def add_child(self, child_node):
        # Контроль уровня
        if child_node.level < self.max_level:
            child_node.level = self.level + 1
            self.childrens.append(child_node)
        else:
            logger.warning("Уровень больше 3 - не добавляем")
            return

    # функция вывода узла
    def __repr__(self):
        ret =  f"id={self.id}  {self.name}  level={self.level}  parent_id={self.parent_id}\n"
        #for child in self.childrens:
        #    ret += " - " + child.__repr__()
        return ret

# функция получения всех потомков узла
def get_childrens(node: TreeNode):
    logger.info(f"get_childrens() -> ...")
    logger.debug(f"node = {node.id} - {node.name}")
    node_list = [node]

    # проходим по всем потомкам
    for child in node.childrens:
        logger.debug(f"child = {child.id} - {child.name}")
        # если уровень потомка меньше или равен 3, то добавляем его потомков в список
        if child.level <= 3:
            a = get_childrens(child)
            node_list += a
        else:
            break
    logger.debug(f"node_list = {node_list}")
    return node_list


# Возвращает список организаций по ID деятельности -----------------------------------------------------------------------------------------------------------------------
def get_organizations_by_activity(
        db: Session, 
        activity_id: int
) -> List[OrganizationSchema]:
    logger.info(f"get_organizations_by_activity() -> ...")
    logger.debug(f"Запрос на получение организаций по ID деятельности: activity_id={activity_id} ...")

    s = f"""
        SELECT b.id, b.name
        FROM organization_activity a
        LEFT JOIN organizations b ON (a.organization_id = b.id)
        WHERE a.activity_id = {activity_id}
        ORDER BY b.name
    """
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    logger.debug(f"recs: {recs}")
    organizations = []
    for rec in recs:
        logger.debug(f"rec: {rec}")
        organization = OrganizationSchema(id=rec.id, name=rec.name)
        logger.debug(f"organization: {organization}")
        # проверка на дублирование
        bSame = False
        for org in organizations:
            if org.id == organization.id:
                bSame = True
                break
        if not bSame:
            organizations.append(organization)
    logger.debug(f"organizations: {organizations}")
    logger.debug(f"End get_organizations_by_activity() -> ...")
    return organizations


# Возвращает список организаций по названию -----------------------------------------------------------------------------------------------------------------------
def get_organizations_by_name(
        db: Session, 
        name: str
) -> List[OrganizationSchema]:
    logger.info(f"get_organizations_by_name() -> ...")
    logger.debug(f"Запрос на получение организаций по названию: name={name} ...")
    s = f"""
        SELECT b.id, b.name
        FROM organizations b
        WHERE UPPER(b.name) LIKE UPPER('%{name}%')
        ORDER BY b.name
    """
    logger.debug(f"В SQLITE запрос использующий UPPER() - для кирилицы не работает, значит, что она не поддерживает символы за пределами диапазона ASCII")
    query = text(s)
    logger.debug(f"query: {query}")
    result = db.execute(query)
    recs = result.fetchall()
    logger.debug(f"recs: {recs}")
    organizations = []
    for rec in recs:
        organization = OrganizationSchema(id=rec.id, name=rec.name)
        organizations.append(organization)
    logger.debug(f"organizations: {organizations}")
    logger.debug(f"End get_organizations_by_name() -> ...")
    return organizations

# ==============================================================================================================================
# Главная страница ------------------------------------------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    """
        Главная страница проекта Nebus. <br>
        запуск в браузере: http://localhost:8000/
    """
    logger.info("Главная страница.")
    # Список всех зданий
    buildings = get_all_buildings(db=db)
    logger.debug(f"buildings: {buildings}")
    activities = get_activities(db=db)
    logger.debug(f"activities: {activities}")
    # Список зданий и деятельностей
    buildings_list = []
    activities_list = []
    for building in buildings:
        buildings_list.append({"id": building.id, "address": building.address})
    for activity in activities:
        activities_list.append({
            "id": activity.id, 
            "name": activity.name, 
            "parent_id": activity.parent_id, 
            "level": activity.level
        })
    # Данные для шаблона
    data = {"api_key": API_KEY, 
            "request": request, 
            "buildings": buildings_list, 
            "activities": activities_list
            }
    return templates.TemplateResponse("index.html", data)


# Информация -------------------------------------------------------------------------------------------------------------
@router.get("/info", response_class=HTMLResponse)
def read_info(request: Request):
    """
        Информация о проекте Nebus.<br>
        запуск в браузере: http://localhost:8000/info
    """
    return templates.TemplateResponse("info.html", {"request": request})


# Возвращает список организаций по ID здания ---------------------------------------------------------------------------------
@router.post("/organizations/building", response_class=HTMLResponse)
def post_organizations_by_building(
    building_id: int = Form(...),
    api_key: str = Form(...),  # API ключ
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает список организаций по ID здания.<br>
        building_id - ID здания<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"post_organizations_by_building() -> ...")
    logger.debug(f"Запрос на получение организаций по ID здания: building_id={building_id} ...")

    # Проверка API ключа
    verify_api_key(api_key)

    # Получение списка организаций по ID здания
    organizations = get_organizations_by_building(db=db, building_id=building_id)
    logger.debug(f"organizations: {organizations}")

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
    for organization in organizations:
        logger.debug(f"organization: {organization}")

        # Получение телефонов организации
        phones = get_phones(db, organization.id)
        phones_list = ""
        for phone in phones:
            logger.debug(f"phone: {phone}")
            phones_list += f"{phone.phone_number}<br>"
        logger.debug(f"phones_list: {phones_list}")

        # Получение деятельностей организации
        activities = get_activities(db=db, organization_id = organization.id)
        logger.debug(f"activities: {activities}")
        # Список всех деятельностей организации
        activities_names = ""
        # Цикл по всем деятельностям
        for activity in activities:
            logger.debug(f"activity: {activity}")
            activities_names += f"[{activity.level}] {activity.name}<br>"

        # Получение адреса организации
        building = get_building_by_organization_id(db=db, organization_id=organization.id)
        logger.debug(f"building: {building}")

        # Формирование строки таблицы
        sRow = f"""
            <tr>
                <td scope="row">{organization.id}</td>
                <td>{organization.name}</td>
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


# Добавление новой деятельности -----------------------------------------------------------------------------------------------------------------------
@router.post("/add_activity/", response_model=ActivitySchema)
def add_activity(
    parent_id: int = Form(...),
    name: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
) -> ActivitySchema:
    """
        Добавление новой деятельности с проверкой уровня вложенности.<br>
        parent_id - ID родителя деятельности<br>
        name - название деятельности<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"add_activity() -> ...")
    logger.debug(f"Запрос на добавление новой деятельности: parent_id={parent_id}, name={name} ...")
    """Добавление новой деятельности с проверкой уровня вложенности."""

    # Проверка API ключа
    verify_api_key(api_key)

    # Проверка уровня родителя деятельности
    if parent_id is not None:
        activity = get_activity_by_id(db=db, activity_id=parent_id)
        if (activity is not None) and (activity.level >= 3):
            raise HTTPException(status_code=400, detail="ERROR: Уровень вложенности родителя деятельности не должен превышать 3!")

    # Добавление новой деятельности
    new_activity = Activity(name=name, parent_id=parent_id)
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


# Возвращает список организаций по ID деятельности -----------------------------------------------------------------------------------------------------------------------
@router.post("/organizations/activity", response_class=HTMLResponse)
def post_organizations_by_activity(
    activity_id: int = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает список организаций по ID деятельности.<br>
        activity_id - ID деятельности<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"post_organizations_by_activity() -> ...")
    logger.debug(f"Запрос на получение организаций по ID деятельности: activity_id={activity_id} ...")
    # Проверка API ключа
    verify_api_key(api_key)

    # Получение списка организаций по ID деятельности
    organizations = get_organizations_by_activity(db=db, activity_id=activity_id)
    logger.debug(f"organizations: {organizations}")
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
    for organization in organizations:
        logger.debug(f"organization: {organization}")
        # Получение телефонов организации
        phoneSchemas = get_phones(db, organization.id)
        logger.debug(f"phoneSchemas: {phoneSchemas}")
        phones_list = ""
        for phone in phoneSchemas:
            phones_list += f"{phone.phone_number}<br>"

        # Получение деятельностей организации
        activitySchemas = get_activities(db=db, organization_id = organization.id)
        logger.debug(f"activitySchemas: {activitySchemas}")    
        activities_list = ""
        for activity in activitySchemas:
            activities_list += f"[{activity.level}] {activity.name}<br>"

        # Получение здания организации
        building = get_building_by_organization_id(db=db, organization_id=organization.id)
        logger.debug(f"BuildingSchema: {building}")

        sRow = f"""
            <tr>
                <td scope="row">{organization.id}</td>
                <td>{organization.name}</td>
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


# Возвращает список организаций по координатам и радиусу -----------------------------------------------------------------------------------------------------------------------
@router.post("/organizations/nearby", response_class=HTMLResponse)
def post_organizations_nearby(
    latitude: float = Form(...), 
    longitude: float = Form(...), 
    radius: float = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает список организаций по координатам (latitude, longitude) и радиусу (radius) в км.<br>
        latitude - широта<br>
        longitude - долгота<br>
        radius - радиус в км.<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"post_organizations_nearby() -> ...")
    logger.debug(f"Запрос на получение организаций по координатам и радиусу: latitude={latitude}, longitude={longitude}, radius={radius}, api_key={api_key} ...")

    # Проверка API ключа
    verify_api_key(api_key)

    # Получение всех зданий
    buildings = db.query(Building).all()
    logger.debug(f"all buildings: {buildings}")

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
    for building in buildings:
        logger.debug(f"building: {building}")
        # расстояние в километрах
        d = distance(latitude, longitude, building.latitude, building.longitude)/1000
        logger.debug(f"distance: {d}")
        # если расстояние меньше радиуса, то добавляем в список
        if d <= radius:
            logger.debug(f"building: {building.id}, {building.address}, {round(d, 1)} км.")
            organizations = get_organizations_by_building(db=db, building_id=building.id)
            logger.debug(f"all organizations in building: {organizations}")
            for organization in organizations:
                logger.debug(f"organization: {organization}")
                phoneSchemas = get_phones(db, organization.id)
                logger.debug(f"phoneSchemas: {phoneSchemas}")
                phones_list = ""
                for phone in phoneSchemas:
                    phones_list += f"{phone.phone_number}<br>"

                activitySchemas = get_activities(db=db, organization_id = organization.id)
                logger.debug(f"activitySchemas: {activitySchemas}")    
                activities_list = ""
                for activity in activitySchemas:
                    activities_list += f"[{activity.level}] {activity.name}<br>"

                sRow = f"""
                    <tr>
                        <td scope="row">{organization.id}</td>
                        <td>{organization.name}</td>
                        <td>{building.address} ({round(d, 1)} км.)</td>
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


# Возвращает организацию по ID -----------------------------------------------------------------------------------------------------------------------
@router.post("/organization/id", response_class=HTMLResponse)
def post_organization_by_id(
    organization_id: int = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает организацию по ID.<br>
        organization_id - ID организации<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"post_organization_by_id() -> ...")
    logger.debug(f"Запрос на получение организации по ID: organization_id={organization_id} ...")
    verify_api_key(api_key)

    # Получение организации по ID
    organization = get_organization(db=db, organization_id=organization_id)
    logger.debug(f"organization: {organization}")

    # Получение здания по ID организации
    building = get_building_by_organization_id(db=db, organization_id=organization.id)
    logger.debug(f"building: {building}")

    # Получение телефонов организации
    phones = get_phones(db, organization.id)
    logger.debug(f"phones: {phones}")
    phones_list = ""
    for phone in phones:
        phones_list += f"{phone.phone_number}<br>"

    # Получение деятельностей организации
    activities = get_activities(db=db, organization_id = organization.id)
    logger.debug(f"activities: {activities}")
    activities_list = ""
    for activity in activities:
        activities_list += f"[{activity.level}] {activity.name}<br>"

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

    # Формирование строки таблицы
    sRow = f"""
        <tr>
            <td scope="row">{organization.id}</td>
            <td>{organization.name}</td>
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


# Возвращает организации по названию деятельности ----------------------------------------------------------------------------------------------------
@router.post("/activity/level", response_class=HTMLResponse)
def activity_level(
    activity_id: int = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает организацию по названию деятельности.<br>
        activity_id - ID деятельности<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"activity_level() -> ...")
    logger.debug(f"Запрос на получение организаций по названию деятельности: activity_id={activity_id} ...")
    verify_api_key(api_key)

    # Получение всех деятельностей
    all_activitys = get_activities(db=db)
    #print(f"all_activitys: {all_activitys}")

    # создаем словарь узлов
    tree_nodes = {}
    for item in all_activitys:
        logger.debug(f"item: {item}")
        # создаем узел
        node = TreeNode(name=item.name, level=item.level, id=item.id, parent_id=item.parent_id)
        logger.debug(f"node: {node}")
        if node.level > 1:
            #print("ищем родителя ...")
            for key in tree_nodes:
                p = tree_nodes[key]
                #print(f"p: {p}")
                if p.id == node.parent_id:
                    #print("Нашли - добавляем в потомков ...")
                    p.childrens.append(node)
                    break
        # добавляем в словарь узлов
        tree_nodes[node.id] = node

    logger.debug(f"Вывод словаря tree_nodes:")
    logger.debug(f"{tree_nodes}")

    logger.debug(f"Получить всех потомков узла [{tree_nodes[activity_id].name}]:")
    aActivity_List = get_childrens(tree_nodes[activity_id])
    logger.debug(aActivity_List)

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
    organizations = []
    for items in aActivity_List:
        logger.debug(f"items: {items}")
        orgs = get_organizations_by_activity(db=db, activity_id=items.id)
        organizations += orgs
    logger.debug(f"-1- organizations: {organizations}")


    seen = set()
    unique_organizations = []
    for org in organizations:
        logger.debug(f"org: {org}")
        if org.id not in seen:
            seen.add(org.id)
            unique_organizations.append(org)
    logger.debug(f"-2- unique_organizations: {unique_organizations}")

    for org in unique_organizations:
        logger.debug(f"org: {org}")
        building = get_building_by_organization_id(db=db, organization_id=org.id)
        logger.debug(f"BuildingSchema: {building}")

        phones = get_phones(db, org.id)
        logger.debug(f"phones: {phones}")
        phones_list = ""
        for phone in phones:
            phones_list += f"{phone.phone_number}<br>"

        activities = get_activities(db=db, organization_id = org.id)
        logger.debug(f"activitySchemas: {activities}")    
        activities_list = ""
        for activity in activities:
            activities_list += f"[{activity.level}] {activity.name}<br>"

        sRow = f"""
            <tr>
                <td scope="row">{org.id}</td>
                <td>{org.name}</td>
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


# Возвращает организации по названию -----------------------------------------------------------------------------------------------------------------------
@router.post("/organizations/search_by_name", response_class=HTMLResponse)
def search_organizations_by_name(
    name: str = Form(...), 
    api_key: str = Form(...), 
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
        Возвращает организации по названию (можно кратко).<br>
        name - название организации<br>
        api_key - API ключ<br>
        db - сессия базы данных<br>
    """
    logger.info(f"search_organizations_by_name() -> ...")
    logger.debug(f"Запрос на получение организаций по названию: name={name} ...")
    verify_api_key(api_key)

    organizations = get_organizations_by_name(db=db, name=name)
    logger.debug(f"organizations: {organizations}")

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
    for organization in organizations:
        building = get_building_by_organization_id(db=db, organization_id=organization.id)
        logger.debug(f"BuildingSchema: {building}")

        activities = get_activities(db=db, organization_id = organization.id)
        logger.debug(f"activitySchemas: {activities}")    
        activities_list = ""
        for activity in activities:
            activities_list += f"[{activity.level}] {activity.name}<br>"

        phones = get_phones(db, organization.id)
        logger.debug(f"phones: {phones}")
        phones_list = ""
        for phone in phones:
            phones_list += f"{phone.phone_number}<br>"

        sRow = f"""
            <tr>
                <td scope="row">{organization.id}</td>
                <td>{organization.name}</td>
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
    return HTMLResponse(content=sTable)

