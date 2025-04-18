from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_cors import CORS
from gpt_eval_api_flow import (
    init_user_session,
    get_next_question,
    evaluate_answer,
    generate_report,
    is_quiz_complete
)

app = Flask(__name__, static_url_path="/static", static_folder="static")
CORS(app)

@app.route("/")
def root():
    return redirect("/static/quiz_ui_web.html")

@app.route("/api/start", methods=["POST"])
def start_quiz():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        if not name or not email:
            return jsonify({"error": "이름과 이메일이 필요합니다."}), 400
        init_user_session(name, email)
        return jsonify({"message": "시작됨"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/next-question", methods=["GET"])
def next_question():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "이메일이 누락되었습니다."}), 400
        question = get_next_question(email)
        return jsonify(question)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    try:
        data = request.get_json()
        email = data.get("email")
        answer = data.get("answer")
        if not email or not answer:
            return jsonify({"error": "이메일과 답변이 필요합니다."}), 400
        result = evaluate_answer(email, answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/report", methods=["GET"])
def report():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "이메일이 필요합니다."}), 400
        report_data = generate_report(email)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Render 배포용 포트 설정
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
