from pony.orm import Database, Required, Json

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    user_id = Required(int, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """Бронь авиабилета"""
    name = Required(str)
    city_from = Required(str)
    city_to = Required(str)
    flight = Required(str)
    seats = Required(str)
    comment = Required(str)
    email = Required(str)
    phone = Required(str)


db.generate_mapping(create_tables=True)
