
from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Google Sheets Webhook URL
GOOGLE_SHEETS_WEBHOOK = "https://script.google.com/macros/s/YOUR_WEB_APP_URL/exec"  # TODO: Replace with your actual URL

@app.route("/")
def home():
    return "WiseCollector GPT 평가 서버가 실행 중입니다."

@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        data = request.json
        print("수신된 평가 결과:", data)

        # 날짜 자동 설정
        if "진단일" not in data:
            data["진단일"] = datetime.now().strftime("%Y-%m-%d")

        # Google Sheets로 POST 전송
        response = requests.post(GOOGLE_SHEETS_WEBHOOK, json=data)
        return jsonify({
            "status": "success",
            "google_sheets_response": response.text
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
