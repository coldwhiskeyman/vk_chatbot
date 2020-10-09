import requests
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = 'files/ticket_template.png'
FONT_PATH = 'files/Roboto-Regular.ttf'

BLACK = (0, 0, 0, 255)
AVATAR_SIZE = 100
AVATAR_OFFSET = (440, 80)


def generate_ticket(city_from, city_to, flight, name, email):
    base = Image.open(TEMPLATE_PATH).convert('RGBA')
    font = ImageFont.truetype(FONT_PATH, 14)
    date = flight.split()[0].replace('-', '.')

    draw = ImageDraw.Draw(base)
    draw.text((45, 125), name.upper(), font=font, fill=BLACK)
    draw.text((45, 195), city_from.upper(), font=font, fill=BLACK)
    draw.text((45, 262), city_to.upper(), font=font, fill=BLACK)
    draw.text((285, 262), date.upper(), font=font, fill=BLACK)

    response = requests.get(f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}')
    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)

    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


if __name__ == '__main__':
    generate_ticket('Moscow', 'London', '07-07-2020 Tue 18:00', 'Лев Лещенко', 'lyovasinger@mail.ru')
