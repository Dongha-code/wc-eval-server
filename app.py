
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

import openai  # 맨 위에 추가
import json     # 이미 있으면 생략 가능

# GPT API 키 설정
client = openai.OpenAI(api_key="sk-여기에-본인의-API-키를-붙여넣기")

# Function 정의 (이름, 이메일, 점수 등 포함)
functions = [
    {
        "name": "submit_evaluation_result",
        "description": "WiseCollector 진단 결과를 자동 제출합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "이름": {"type": "string"},
                "이메일": {"type": "string"},
                "진단일": {"type": "string"},
                "레벨": {"type": "string"},
                "정답률": {"type": "string"},
                "STEP1": {"type": "number"},
                "STEP2": {"type": "number"},
                "STEP3": {"type": "number"},
                "STEP4": {"type": "number"},
                "STEP5": {"type": "number"},
                "STEP6": {"type": "number"},
                "STEP7": {"type": "number"},
                "STEP8": {"type": "number"},
                "STEP9": {"type": "number"},
                "추천STEP": {"type": "string"},
                "강점요약": {"type": "string"},
                "약점요약": {"type": "string"},
                "전체평가요약": {"type": "string"}
            },
            "required": [
                "이름", "이메일", "진단일", "레벨", "정답률",
                "STEP1", "STEP2", "STEP3", "STEP4", "STEP5",
                "STEP6", "STEP7", "STEP8", "STEP9",
                "추천STEP", "강점요약", "약점요약", "전체평가요약"
            ]
        }
    }
]

@app.route("/submit", methods=["POST"])
def submit():
    try:
        user_data = request.json
        print("✅ 제출된 사용자 응답:", user_data)

        # GPT 메시지 구성
        messages = [
            {
                "role": "system",
                "content": "너는 WiseCollector 평가 시스템이야. 응답을 평가하고 결과를 JSON으로 자동 제출해야 해."
            },
            {
                "role": "user",
                "content": f"{user_data['이름']}, 이메일 {user_data['이메일']}, 정답률 {user_data['정답률']}%, " +
                           ", ".join([f"STEP{i}={user_data[f'STEP{i}']}" for i in range(1, 10)])
            }
        ]

        # GPT 호출
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[{"type": "function", "function": functions[0]}],
            tool_choice={"type": "function", "function": {"name": "submit_evaluation_result"}}
        )

        # GPT 리포트 → /evaluate로 전송
        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            args.setdefault("진단일", datetime.now().strftime("%Y-%m-%d"))

            # 내부 Webhook 전송
            res = requests.post("http://localhost:8080/evaluate", json=args)

            return jsonify({"status": "success", "응답": args, "저장결과": res.text}), 200
        else:
            return jsonify({"status": "fail", "reason": "GPT가 결과를 반환하지 않았습니다."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
