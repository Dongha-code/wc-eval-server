from flask import Flask, request, jsonify
from datetime import datetime
import json, openai, os, requests
from dotenv import load_dotenv
from gpt_function_schema import functions
from gpt_eval_api_flow import generate_next_question, evaluate_answer, generate_report, session

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK")
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GPT 진단 서버 실행 중"

@app.route("/api/start", methods=["POST"])
def start():
    data = request.json
    session["name"] = data["name"]
    session["email"] = data["email"]
    session["current"] = 0
    session["answers"] = []
    return jsonify({"status": "ready"})

@app.route("/api/next-question", methods=["GET"])
def next_question():
    try:
        question = generate_next_question()
        return jsonify({
            "question": question["question"],
            "step": question["step"],
            "number": session["current"] + 1
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    try:
        data = request.json
        current = session["current"]
        question = session["questions"][current]["question"]
        step = session["step_sequence"][current]
        answer = data["answer"]

        feedback = evaluate_answer(question, answer, step)
        session["answers"].append({
            "step": step,
            "question": question,
            "answer": answer,
            "feedback": feedback
        })
        session["current"] += 1
        complete = session["current"] >= 30

        return jsonify({
            "complete": complete,
            "feedback": feedback
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/report", methods=["GET"])
def report():
    try:
        report_data = generate_report(session["name"], session["email"], session["answers"])
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
