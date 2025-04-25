from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import swisseph as swe
import datetime
import pytz

def generate_chart_text(birth_date, birth_time, birth_place):
    try:
        # Проверка даты
        try:
            parsed_date = datetime.datetime.strptime(birth_date, "%d.%m.%Y")
        except ValueError:
            return "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например, 14.03.1992)"

        # Проверка времени
        try:
            parsed_time = datetime.datetime.strptime(birth_time, "%H:%M")
        except ValueError:
            return "❌ Неверный формат времени. Используйте формат ЧЧ:ММ (например, 15:30)"

        # Геолокация
        geolocator = Nominatim(user_agent="astro_bot")
        try:
            location = geolocator.geocode(birth_place, timeout=10)
        except GeocoderTimedOut:
            return "⚠️ Время ожидания геолокации истекло. Попробуйте ещё раз."
        if not location:
            return "❌ Место не найдено. Укажите город и страну точнее (например: Москва, Россия)."

        latitude = location.latitude
        longitude = location.longitude

        # Часовой пояс
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        timezone = pytz.timezone(timezone_str or "UTC")

        dt = timezone.localize(datetime.datetime(
            parsed_date.year, parsed_date.month, parsed_date.day,
            parsed_time.hour, parsed_time.minute
        ))
        utc_dt = dt.astimezone(pytz.utc)
        decimal_hour = utc_dt.hour + utc_dt.minute / 60
        jd = swe.julday(parsed_date.year, parsed_date.month, parsed_date.day, decimal_hour)

        swe.set_ephe_path("ephe")
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')

        zodiac_signs = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
                        "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

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

        def get_house(pos_deg):
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

        # Формируем вывод
        result = f"Натальная карта:\nДата рождения (UTC): {utc_dt.strftime('%Y-%m-%d %H:%M')}\nМесто: {birth_place} (lat: {latitude:.4f}, lon: {longitude:.4f})\n"
        result += "-" * 50 + "\n"

        for i, pid in enumerate(planet_ids):
            pos, _ = swe.calc_ut(jd, pid)
            total_deg = pos[0] % 360
            sign_index = int(total_deg // 30)
            deg_in_sign = total_deg % 30
            house = get_house(total_deg)
            result += f"{planet_names[i]:<12} — {deg_in_sign:>5.2f}° {zodiac_signs[sign_index]}, дом {house}\n"

        # Южный Узел
        pos, _ = swe.calc_ut(jd, swe.TRUE_NODE)
        south_deg = (pos[0] + 180) % 360
        s_sign = int(south_deg // 30)
        s_deg = south_deg % 30
        s_house = get_house(south_deg)
        result += f"{'Юж. Узел':<12} — {s_deg:>5.2f}° {zodiac_signs[s_sign]}, дом {s_house}\n"

        return result

    except Exception as e:
        return f"⚠️ Произошла ошибка при расчёте карты: {str(e)}"
