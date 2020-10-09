"""
Handler - функция, которая принимает на вход text (текст входящего сообщения)
и context (dict), а возвращает bool: True, если шаг пройден, False, если данные введены неверно.
"""

import re
import datetime

from dispatcher import get_city, get_flights, get_date_from_str
from flights import FLIGHTS
from generate_ticket import generate_ticket

re_name = re.compile(r'^[\w\-\s]{3,40}$')
re_city = re_name
re_email = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')
re_date = re.compile(r'^\d{2}-\d{2}-\d{4}$')
re_phone = re.compile(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$')


def handle_name(text, context):
    match = re.match(re_name, text)
    if match:
        context['name'] = text
        return True
    else:
        return False


def handle_email(text, context):
    matches = re.findall(re_email, text)
    if len(matches) > 0:
        context['email'] = matches[0]
        return True
    else:
        return False


def handle_city_from(text, context):
    match = re.match(re_city, text)
    if match:
        try:
            city = get_city(match.group())
        except ValueError:
            cities = ', '.join(list(FLIGHTS.keys()))
            context['city_from'] = cities
            return False
        context['city_from'] = city
        return True
    else:
        return False


def handle_city_to(text, context):
    match = re.match(re_city, text)
    if match:
        try:
            city = get_city(match.group())
        except ValueError:
            cities = ', '.join(list(FLIGHTS[context['city_from']].keys()))
            context['city_to'] = cities
            return False
        if city not in list(FLIGHTS[context['city_from']].keys()):
            context['stop'] = True
            return False
        context['city_to'] = city
        return True
    else:
        return False


def handle_date(text, context):
    match = re.match(re_date, text)
    if match:
        if get_date_from_str(text) < datetime.date.today():
            return False
        context['date'] = text
        context['flight'] = get_flights(context)
        context['flight_text'] = ''
        for index, flight in enumerate(context['flight']):
            context['flight_text'] += str(index + 1) + '. ' + ' '.join(flight) + '\n'
        return True
    else:
        return False


def handle_flight(text, context):
    pattern = '[1-{}]'.format(len(context['flight']))
    if re.match(pattern, text):
        context['flight'] = ' '.join(context['flight'][int(text) - 1])
        return True
    else:
        return False


def handle_seats(text, context):
    if re.match(r'[1-5]', text):
        context['seats'] = text
        return True
    else:
        return False


def handle_comment(text, context):
    context['comment'] = text
    return True


def handle_confirm(text, context):
    if text == 'да':
        return True
    elif text == 'нет':
        context['stop'] = True
        return False


def handle_phone(text, context):
    match = re.match(re_phone, text)
    if match:
        context['phone'] = text
        return True
    else:
        return False


def generate_ticket_handler(text, context):
    return generate_ticket(city_from=context['city_from'],
                           city_to=context['city_to'],
                           flight=context['flight'],
                           name=context['name'],
                           email=context['email'])
