from flask import Flask, request, jsonify
from flask_cors import CORS
from gpt_eval_api_flow import (
    init_user_session,
    get_next_question,
    is_quiz_complete,
    evaluate_answer,
    generate_report,
    submit_user_answer,
    user_sessions
)
from threading import Thread

app = Flask(__name__)
CORS(app)

@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json()
    init_user_session(data["name"], data["email"])
    return jsonify({"status": "started"})

@app.route("/api/next-question", methods=["GET"])
def api_next_question():
    email = request.args.get("email")
    user = user_sessions.get(email)
    if not user:
        return jsonify({"error": "세션 없음"}), 400

    if "next_question" in user:
        next_q = user.pop("next_question")
        return jsonify(next_q)
    else:
        return jsonify({"status": "loading"}), 202

@app.route("/api/submit-answer", methods=["POST"])
def api_submit_answer():
    data = request.get_json()
    email = data["email"]
    answer = data["answer"]
    submit_user_answer(email, answer)

    def background_next():
        user = user_sessions[email]
        user["next_question"] = get_next_question(user)

    Thread(target=background_next).start()
    return jsonify({"status": "submitted"})

@app.route("/api/report", methods=["GET"])
def api_report():
    email = request.args.get("email")
    return jsonify(generate_report(email))
