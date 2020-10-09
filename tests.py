from copy import deepcopy
from datetime import date
from unittest import TestCase, main
from unittest.mock import patch, Mock

from vk_api.bot_longpoll import VkBotMessageEvent
from pony.orm import db_session, rollback

from bot import Bot
import settings
from handlers import handle_date, handle_flight
from generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class TestBot(TestCase):

    RAW_EVENT = {'type': 'message_new', 'object': {
        'message': {'date': 1592759547, 'from_id': 2541828, 'id': 36, 'out': 0, 'peer_id': 2541828,
                    'text': 'thats dangerous', 'conversation_message_id': 36, 'fwd_messages': [], 'important': False,
                    'random_id': 0, 'attachments': [], 'is_hidden': False},
        'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'], 'keyboard': True,
                        'inline_keyboard': True, 'lang_id': 0}}, 'group_id': 96449677,
                 'event_id': '7366b20f764ddaffd12a9821d6c35e39fef62484'}

    def test_run(self):
        count = 5
        obj = {}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'), patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
            bot = Bot('', '')
            bot.on_event = Mock()
            bot.send_image = Mock()
            bot.run()

            bot.on_event.assert_called()
            bot.on_event.assert_any_call(obj)
            assert bot.on_event.call_count == count

    INPUTS = [
        'Привет',
        '/ticket',
        'москва',
        'парж',
        'париж',
        date.today().strftime('%d-%m-%Y'),
        '1',
        '2',
        'хочу место у окна',
        'Валерий Леонтьев',
        'да',
        'valera@valera.ru'
    ]

    test_context = {'city_from': 'Moscow', 'city_to': 'Paris'}
    handle_date(date.today().strftime('%d-%m-%Y'), test_context)
    handle_flight('1', test_context)

    EXPECTED_OUTPUTS = [
        settings.INTENTS[0]['answer'],
        settings.SCENARIOS['ticket']['steps']['step1']['text'],
        settings.SCENARIOS['ticket']['steps']['step2']['text'],
        settings.SCENARIOS['ticket']['steps']['step2']['failure_text'].format(city_to='London, Paris'),
        settings.SCENARIOS['ticket']['steps']['step3']['text'],
        settings.SCENARIOS['ticket']['steps']['step4']['text'].format(
            flight_text=test_context['flight_text']),
        settings.SCENARIOS['ticket']['steps']['step5']['text'],
        settings.SCENARIOS['ticket']['steps']['step6']['text'],
        settings.SCENARIOS['ticket']['steps']['step7']['text'],
        settings.SCENARIOS['ticket']['steps']['step8']['text'].format(
            city_from='Moscow', city_to='Paris', flight=test_context['flight'], seats='2',
            comment='хочу место у окна', name='Валерий Леонтьев'),
        settings.SCENARIOS['ticket']['steps']['step9']['text'],
        settings.SCENARIOS['ticket']['steps']['step10']['text']
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with open('files/avatar-example.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()
        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket(
                'Moscow', 'London', '07-07-2020 Tue 18:00', 'Лев Лещенко', 'lyovasinger@mail.ru')
        with open('files/ticket-example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes


if __name__ == '__main__':
    main()
