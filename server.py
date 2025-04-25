from flask import Flask, request, jsonify
from astro_chart_generator import (
    validate_date, validate_time, validate_place,
    generate_chart_json
)

app = Flask(__name__)


def format_chart_text(chart):
    result = chart["result"]
    lines = []

    lines.append(f"Натальная карта:")
    lines.append(f"Дата рождения (UTC): {result['birth_date_utc']}")
    place = result["place"]
    lines.append(f"Место: {place['name']} (lat: {place['latitude']}, lon: {place['longitude']})")
    lines.append(f"Часовой пояс: {place['timezone']}")
    lines.append("-" * 50)

    lines.append("Планеты:")
    for name, info in result["planets"].items():
        retro = " R" if info["retrograde"] else ""
        lines.append(f"{name:<12} — {info['degree']:.2f}° {info['sign']}, дом {info['house']}{retro}")
    
    lines.append("\nКуспиды домов:")
    for house in result["houses"]:
        lines.append(f"{house['house']:>2} дом: {house['degree']:.2f}° {house['sign']}")

    lines.append("\nАспекты:")
    for asp in result["aspects"]:
        orb_str = f"{asp['orb']:+.2f}°"
        lines.append(f"{asp['planet1']} — {asp['planet2']}: {asp['aspect']} ({orb_str})")

    return "\n".join(lines)


@app.route("/validate/date", methods=["POST"])
def validate_birth_date():
    data = request.get_json()
    birth_date = data.get("birth_date", "")
    result = validate_date(birth_date)
    if result is True:
        return jsonify({"valid": True})
    return jsonify({"valid": False, "error": result}), 400


@app.route("/validate/time", methods=["POST"])
def validate_birth_time():
    data = request.get_json()
    birth_time = data.get("birth_time", "")
    result = validate_time(birth_time)
    if result is True:
        return jsonify({"valid": True})
    return jsonify({"valid": False, "error": result}), 400


@app.route("/validate/place", methods=["POST"])
def validate_birth_place():
    data = request.get_json()
    birth_place = data.get("birth_place", "")
    result = validate_place(birth_place)
    if result["valid"]:
        return jsonify({
            "valid": True,
            "lat": result["lat"],
            "lon": result["lon"],
            "timezone": result["timezone"]
        })
    return jsonify({"valid": False, "error": result["error"]}), 400


@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.get_json()
    try:
        birth_date = data["birth_date"]
        birth_time = data["birth_time"]
        birth_place = data["birth_place"]

        chart = generate_chart_json(birth_date, birth_time, birth_place)
        text = format_chart_text(chart)

        return jsonify({
            "status": "ok",
            "text": text,
            "chart": chart["result"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)