from datetime import date
import re

from flights import FLIGHTS


def get_city(city_input):
    for char in city_input:
        if not char.isalpha() and char != '-' and char != ' ':
            raise ValueError('Ошибка в названии города')
    city_input = city_input.lower()
    if 'moscow' in city_input or 'москв' in city_input:
        return 'Moscow'
    elif 'paris' in city_input or 'париж' in city_input:
        return 'Paris'
    elif 'london' in city_input or 'лондон' in city_input:
        return 'London'
    elif re.search(r'[nн][eь][wю][\s\-][yй][oо][rр][kк]', city_input) is not None:
        return 'New York'
    else:
        raise ValueError('Неизвестный город или ошибка в названии')


def get_flights(context):
    raw_flight_list = FLIGHTS[context['city_from']][context['city_to']]
    result_flight_list = []
    favoured_date = get_date_from_str(context['date'])
    counter = 0
    for flight in raw_flight_list:
        if counter == 5:
            break
        if favoured_date < get_date_from_str(flight[0]):
            result_flight_list.append(flight)
            counter += 1
    return result_flight_list


def get_date_from_str(date_str):
    year = int(date_str[6:])
    month = int(date_str[3:5])
    day = int(date_str[:2])
    return date(year=year, month=month, day=day)
