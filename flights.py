import datetime
from calendar import Calendar

FLIGHTS = {
    'Moscow': {
        'London': [],
        'Paris': []
    },
    'London': {
        'Moscow': [],
        'Paris': [],
        'New York': []
    },
    'Paris': {
        'London': [],
        'Moscow': [],
        'New York': []
    },
    'New York': {
        'London': [],
        'Paris': []
    }
}

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

this_month = datetime.date.today().month
this_year = datetime.date.today().year


def make_flights_by_day(city_from, city_to, days, time):
    calendar = Calendar()
    for i in range(3):
        for day in calendar.itermonthdates(this_year, this_month + i):
            if day.month == this_month + i and day.day in days:
                date_str = day.strftime('%d-%m-%Y')
                FLIGHTS[city_from][city_to].append(
                    [date_str, WEEKDAYS[day.weekday()], time])


def make_flights_by_weekday(city_from, city_to, days, time):
    calendar = Calendar()
    for i in range(3):
        for day in calendar.itermonthdates(this_year, this_month + i):
            if day.month == this_month + i and day.weekday() in days:
                date_str = day.strftime('%d-%m-%Y')
                FLIGHTS[city_from][city_to].append(
                    [date_str, WEEKDAYS[day.weekday()], time])


make_flights_by_weekday('Moscow', 'London', (0, 2), '10:00')
make_flights_by_weekday('Moscow', 'Paris', (3, 5), '15:00')
make_flights_by_weekday('London', 'Moscow', (0, 2), '16:00')
make_flights_by_day('London', 'Paris', (10, 20), '15:30')
make_flights_by_day('London', 'New York', (5, 15, 25), '11:00')
make_flights_by_day('Paris', 'London', (10, 20), '17:30')
make_flights_by_weekday('Paris', 'Moscow', (3, 5), '11:00')
make_flights_by_day('Paris', 'New York', (6, 16, 26), '12:00')
make_flights_by_day('New York', 'London', (5, 15, 25), '20:00')
make_flights_by_day('New York', 'Paris', (6, 16, 26), '21:00')
