
from flask import Flask, request, jsonify
from datetime import datetime
import requests
import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK")
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GPT 평가 서버가 실행 중입니다."

@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        data = request.json
        print("📥 수신된 평가 데이터:", data)
        return jsonify({"status": "success", "message": "데이터가 정상 수신되었습니다."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[{"type": "function", "function": functions[0]}],
            tool_choice={"type": "function", "function": {"name": "submit_evaluation_result"}}
        )

        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            args.setdefault("진단일", datetime.now().strftime("%Y-%m-%d"))

            res = requests.post(webhook_url, json=args)

            return jsonify({"status": "success", "응답": args, "저장결과": res.text}), 200
        else:
            return jsonify({"status": "fail", "reason": "GPT가 결과를 반환하지 않았습니다."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)
