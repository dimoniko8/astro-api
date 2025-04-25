# server.py

from flask import Flask, request, jsonify
from astro_chart_generator import (
    validate_date, validate_time, validate_place,
    generate_chart_json
)

app = Flask(__name__)

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
        return jsonify(chart)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)