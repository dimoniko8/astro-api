# astro_chart_generator.py

import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz
import swisseph as swe


def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return "Неверный формат даты. Используйте ДД.ММ.ГГГГ"

def validate_time(time_str):
    try:
        datetime.datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return "Неверный формат времени. Используйте ЧЧ:ММ"

def validate_place(place_str):
    try:
        geolocator = Nominatim(user_agent="astro_bot")
        location = geolocator.geocode(place_str, timeout=10)
        if not location:
            return {"valid": False, "error": "Место не найдено. Укажите точнее."}

        tf = TimezoneFinder()
        tz = tf.timezone_at(lat=location.latitude, lng=location.longitude)
        return {
            "valid": True,
            "lat": location.latitude,
            "lon": location.longitude,
            "timezone": tz
        }
    except GeocoderTimedOut:
        return {"valid": False, "error": "Тайм-аут при определении местоположения. Попробуйте снова."}

def generate_chart_json(birth_date, birth_time, birth_place):
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder

    # Разбор даты и времени
    dt = datetime.datetime.strptime(f"{birth_date} {birth_time}", "%d.%m.%Y %H:%M")

    # Геокодирование
    geolocator = Nominatim(user_agent="astro_bot")
    location = geolocator.geocode(birth_place, timeout=10)
    if not location:
        raise ValueError("Место не найдено")

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    timezone = pytz.timezone(timezone_str or "UTC")
    local_dt = timezone.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Расчёт Julian Day
    swe.set_ephe_path("ephe")
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60)

    # Расчёт домов
    cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')

    planet_ids = [
        swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
        swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO,
        swe.TRUE_NODE, swe.MEAN_APOG, 15  # Хирон
    ]
    planet_names = [
        "Солнце", "Луна", "Меркурий", "Венера", "Марс",
        "Юпитер", "Сатурн", "Уран", "Нептун", "Плутон",
        "Сев. Узел", "Лилит", "Хирон"
    ]
    zodiac_signs = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
                    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

    def get_house(pos_deg, cusps):
        for i in range(12):
            start = cusps[i]
            end = cusps[(i + 1) % 12]
            if start < end:
                if start <= pos_deg < end:
                    return i + 1
            else:
                if pos_deg >= start or pos_deg < end:
                    return i + 1
        return 12

    planets = []
    for i, pid in enumerate(planet_ids):
        pos, _ = swe.calc_ut(jd, pid)
        total_deg = pos[0] % 360
        sign_index = int(total_deg // 30)
        deg_in_sign = total_deg % 30
        house = get_house(total_deg, cusps)
        speed = pos[3]
        is_retro = speed < 0

        planets.append({
            "name": planet_names[i],
            "degree": round(deg_in_sign, 2),
            "sign": zodiac_signs[sign_index],
            "house": house,
            "retrograde": is_retro
        })

    # Южный узел
    north_deg = [p for p in planets if p["name"] == "Сев. Узел"][0]["degree"]
    south_deg = (north_deg + 180) % 360
    south_sign_index = int(south_deg // 30)
    south_deg_in_sign = south_deg % 30
    house = get_house(south_deg, cusps)

    planets.append({
        "name": "Юж. Узел",
        "degree": round(south_deg_in_sign, 2),
        "sign": zodiac_signs[south_sign_index],
        "house": house,
        "retrograde": False
    })

    return {
        "result": {
            "birth_date_utc": utc_dt.strftime("%Y-%m-%d %H:%M"),
            "place": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "planets": planets
        },
        "status": "ok"
    }