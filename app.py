from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, openai, os
from dotenv import load_dotenv
from gpt_function_schema import functions
from gpt_flask_api import generate_question, evaluate_answer, generate_report, create_step_sequence

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK")
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)

# 세션 상태
user_session = {
    "name": None,
    "email": None,
    "answers": [],
    "step_sequence": [],
    "current_index": 0,
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
    user_session["current_index"] = 0
    user_session["step_sequence"] = create_step_sequence(total_questions=30)
    return jsonify({"status": "started"})

@app.route("/api/next-question", methods=["GET"])
def next_question():
    try:
        index = user_session["current_index"]
        if index >= len(user_session["step_sequence"]):
            return jsonify({"complete": True})
        step = user_session["step_sequence"][index]
        result = generate_question(step)
        result["step"] = step
        result["index"] = index + 1
        result["total"] = len(user_session["step_sequence"])
        user_session["current_question"] = result
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    try:
        data = request.json
        answer = data["answer"]
        question = user_session["current_question"]["question"]
        step = user_session["step_sequence"][user_session["current_index"]]
        feedback = evaluate_answer(question, answer, step)

        user_session["answers"].append({
            "step": step,
            "question": question,
            "answer": answer,
            "feedback": feedback
        })

        user_session["current_index"] += 1
        complete = user_session["current_index"] >= len(user_session["step_sequence"])

        return jsonify({
            "complete": complete,
            "feedback": feedback,
            "step": step
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
