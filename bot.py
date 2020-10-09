import random
import logging
import requests

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from pony.orm import db_session

import handlers

try:
    import settings
except ImportError:
    exit('DO cp settings.py.default settings.py and set token')
from models import UserState, Registration

log = logging.getLogger('bot')


def configure_logging():
    """Настройка логгирования"""
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    log.setLevel(logging.DEBUG)


class Bot:
    """
    Бот для заказа авиабилетов в vk.com
    Use python 3.7

    Сценарий заказа:
    - спрашиваем город отправления
    - спрашиваем город назначения
    - спрашиваем желаемую дату вылета
    - выдаем ближайшие к дате рейсы, и спрашиваем какой из них подходит
    - спрашиваем количество желаемых мест
    - предлагаем дать комментарий к заказу
    - спрашиваем имя клиента
    - проверяем корректность введенных данных
    - спрашиваем email для связи
    - спрашиваем телефон для связи
    Если шаг не пройден, задаем уточняющий вопрос, пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы VK
        :param token: секретный токен
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Запуск бота"""
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception('Ошибка в обработке события')

    @db_session
    def on_event(self, event):
        """
        Обрабатывает введенные данные
        :param event: VkBotMessageEvent object
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info(
                'Мы пока не умее обрабатывать событие такого типа %s', event.type)
            return

        user_id = event.object.message['peer_id']
        text = event.object.message['text']

        state = UserState.get(user_id=user_id)

        if text in settings.COMMANDS:
            self.check_intents(user_id, text)
        elif state is not None:
            self.continue_scenario(text, state, user_id)
        else:
            self.check_intents(user_id, text)

    def check_intents(self, user_id, text):
        """Проверка возможных запросов"""
        for intent in settings.INTENTS:
            log.debug(f'User gets {intent}')
            if any(token in text.lower() for token in intent['tokens']):
                if intent['answer']:
                    self.send_text(intent['answer'], user_id)
                else:
                    self.start_scenario(user_id, intent['scenario'], text)
                break
        else:
            self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        """Отправка сообщения в VK"""
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id
        )

    def send_image(self, image, user_id):
        """Отправка изображения в VK"""
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id
        )

    def send_step(self, step, user_id, text, context):
        """Проверка шага сценария, для определения механизма отправки"""
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        """Запуск сценария бота"""
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=user_id, scenario_name=scenario_name,
                  step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        """Переход на следующий шаг сценария бота"""
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info(
                    'Зарегистрирован: {name} {city_from} - {city_to} {flight} {seats} seats "{comment}" {phone} {email}'.
                    format(**state.context))
                Registration(city_from=state.context['city_from'],
                             city_to=state.context['city_to'],
                             flight=state.context['flight'],
                             seats=state.context['seats'],
                             comment=state.context['comment'],
                             name=state.context['name'],
                             email=state.context['email'],
                             phone=state.context['phone'], )
                state.delete()

        else:
            if 'stop' in state.context:
                text_to_send = step['stop_scenario'].format(**state.context)
                self.send_text(text_to_send, user_id)
                state.delete()
            else:
                text_to_send = step['failure_text'].format(**state.context)
                self.send_text(text_to_send, user_id)


if __name__ == "__main__":
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
