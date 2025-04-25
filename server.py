from flask import Flask, request, jsonify
import os
import datetime
import json

from astro_chart_generator import generate_chart_text

app = Flask(__name__)

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "requests.log")
os.makedirs(LOG_DIR, exist_ok=True)

def log_request(data):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
        f.write("\n" + "-"*40 + "\n")

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Чтение и логирование тела запроса
        data = request.get_json(force=True)
        log_request(data)

        birth_date = data.get("birth_date")
        birth_time = data.get("birth_time")
        birth_place = data.get("birth_place")

        result = generate_chart_text(birth_date, birth_time, birth_place)
        return jsonify({"result": result, "status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
