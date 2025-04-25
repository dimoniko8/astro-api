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
    import pytz

    day, month, year = map(int, birth_date.split("."))
    hour, minute = map(int, birth_time.split(":"))

    # Геолокация и часовой пояс
    geolocator = Nominatim(user_agent="astro_bot")
    location = geolocator.geocode(birth_place, timeout=10)
    if not location:
        raise ValueError("Место не найдено")

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    tz = pytz.timezone(tz_str or "UTC")

    dt = tz.localize(datetime.datetime(year, month, day, hour, minute))
    utc_dt = dt.astimezone(pytz.utc)
    decimal_hour = utc_dt.hour + utc_dt.minute / 60
    jd = swe.julday(year, month, day, decimal_hour)

    # Эфемериды
    swe.set_ephe_path("ephe")
    cusps, _ = swe.houses(jd, location.latitude, location.longitude)

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
    zodiac_signs = [
        "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
        "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
    ]

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

    # Планеты
    planet_data = {}
    positions = {}
    for i, pid in enumerate(planet_ids):
        pos, _ = swe.calc_ut(jd, pid)
        total_deg = pos[0] % 360
        speed = pos[3]
        is_retro = speed < 0
        sign_index = int(total_deg // 30)
        deg_in_sign = total_deg % 30
        house = get_house(total_deg, cusps)

        positions[planet_names[i]] = total_deg
        planet_data[planet_names[i]] = {
            "sign": zodiac_signs[sign_index],
            "degree": round(deg_in_sign, 2),
            "house": house,
            "retrograde": is_retro
        }

    # Южный узел
    if "Сев. Узел" in positions:
        south_node_deg = (positions["Сев. Узел"] + 180) % 360
        sign_index = int(south_node_deg // 30)
        deg_in_sign = south_node_deg % 30
        house = get_house(south_node_deg, cusps)
        positions["Юж. Узел"] = south_node_deg
        planet_data["Юж. Узел"] = {
            "sign": zodiac_signs[sign_index],
            "degree": round(deg_in_sign, 2),
            "house": house,
            "retrograde": False
        }

    # Куспиды домов
    house_cusps = []
    for i in range(12):
        deg = cusps[i] % 360
        sign_index = int(deg // 30)
        deg_in_sign = deg % 30
        house_cusps.append({
            "house": i + 1,
            "sign": zodiac_signs[sign_index],
            "degree": round(deg_in_sign, 2)
        })

    # Аспекты
    aspects_def = {
        "Соединение": (0, 8),
        "Оппозиция": (180, 8),
        "Трин": (120, 7),
        "Квадрат": (90, 6),
        "Секстиль": (60, 5)
    }

    aspect_list = []
    names = list(positions.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name1 = names[i]
            name2 = names[j]
            deg1 = positions[name1]
            deg2 = positions[name2]
            diff = abs(deg1 - deg2)
            diff = min(diff, 360 - diff)

            for aspect_name, (angle, orb) in aspects_def.items():
                if abs(diff - angle) <= orb:
                    aspect_list.append({
                        "planet1": name1,
                        "planet2": name2,
                        "aspect": aspect_name,
                        "orb": round(diff - angle, 2)
                    })

    return {
        "result": {
            "birth_date_utc": utc_dt.strftime("%Y-%m-%d %H:%M"),
            "place": {
                "name": location.address,
                "latitude": round(location.latitude, 4),
                "longitude": round(location.longitude, 4),
                "timezone": tz_str
            },
            "planets": planet_data,
            "houses": house_cusps,
            "aspects": aspect_list
        },
        "status": "ok"
    }