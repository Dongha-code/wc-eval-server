from flask import Flask, request, jsonify
from datetime import datetime
import requests
import json
import openai
from dotenv import load_dotenv
import os
from gpt_function_schema import functions
from gpt_flask_api import generate_question, evaluate_answer, generate_report

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK")
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)

# 세션용 임시 저장소
user_session = {
    "name": None,
    "email": None,
    "answers": [],
    "current_step": 1,
    "current_question": None
}

@app.route("/")
def index():
    return "✅ GPT 평가 서버가 실행 중입니다."

@app.route("/api/start", methods=["POST"])
def start_quiz():
    data = request.json
    user_session["name"] = data["name"]
    user_session["email"] = data["email"]
    user_session["answers"] = []
    user_session["current_step"] = 1
    return jsonify({"status": "started"})

@app.route("/api/next-question", methods=["GET"])
def next_question():
    try:
        step = f"STEP {user_session['current_step']}"
        result = generate_question(step)
        user_session["current_question"] = result
        result["step"] = step
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    try:
        data = request.json
        answer = data["answer"]
        question = user_session.get("current_question", {}).get("question", "")
        step = f"STEP {user_session['current_step']}"
        feedback = evaluate_answer(question, answer, step)

        user_session["answers"].append({
            "step": step,
            "question": question,
            "answer": answer,
            "feedback": feedback
        })

        user_session["current_step"] += 1
        complete = user_session["current_step"] > 9

        return jsonify({
            "feedback": feedback,
            "step": step,
            "complete": complete
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/report", methods=["GET"])
def report():
    try:
        answers = user_session["answers"]
        name = user_session["name"]
        email = user_session["email"]
        report_data = generate_report(name, email, answers)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit", methods=["POST"])
def submit():
    try:
        user_data = request.json
        print("✅ 제출된 사용자 응답:", user_data)

        messages = [
            {
                "role": "system",
                "content": "너는 WiseCollector 평가 시스템이야. 응답을 평가하고 결과를 JSON으로 자동 제출해야 해. 반드시 한국어로 리포트를 작성해."
            },
            {
                "role": "user",
                "content": f"{user_data['이름']}, 이메일 {user_data['이메일']}, 정답률 {user_data['정답률']}%, " +
                           ", ".join([f"STEP{i}={user_data[f'STEP{i}']}" for i in range(1, 10)])
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ 변경됨
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
    app.run(host="0.0.0.0", port=10000)
