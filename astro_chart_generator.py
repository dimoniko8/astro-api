# astro_chart_generator.py

import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

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
    # Здесь должна быть логика генерации натальной карты и возвращения в JSON.
    return {
        "result": f"Натальная карта: {birth_date} {birth_time} в {birth_place}",
        "status": "ok"
    }