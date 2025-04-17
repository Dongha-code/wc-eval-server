from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gpt_eval_api_flow import (
    init_user_session,
    submit_user_answer,
    get_next_question,
    is_quiz_complete,
    get_user_result_summary
)
from threading import Thread
import os

app = Flask(__name__, static_folder="static")
CORS(app)

# 사용자 세션 저장소
user_sessions = {}

# 정적 파일 라우팅
@app.route("/")
def index():
    return send_from_directory("static", "quiz_ui_web.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# 초기 시작
@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    if not email or not name:
        return jsonify({"error": "이름과 이메일이 필요합니다."}), 400

    user_sessions[email] = init_user_session(name, email)
    first_question = get_next_question(user_sessions[email])
    return jsonify(first_question)

# 답안 제출 - 비동기 처리 방식
@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    data = request.get_json()
    email = data.get("email")
    answer = data.get("answer")

    if email not in user_sessions:
        return jsonify({"error": "세션이 존재하지 않습니다."}), 400

    # 답안 저장
    submit_user_answer(email, answer)

    # 다음 문제 비동기 생성
    def generate_next():
        user_sessions[email]["next_question"] = get_next_question(user_sessions[email])

    Thread(target=generate_next).start()

    return jsonify({"message": "답안 제출 완료"})

# 다음 문제 요청 (캐시된 문제 반환)
@app.route("/api/next-question", methods=["GET"])
def api_next_question():
    email = request.args.get("email")

    if email not in user_sessions:
        return jsonify({"error": "세션이 없습니다."}), 400

    if "next_question" in user_sessions[email]:
        next_q = user_sessions[email].pop("next_question")
        return jsonify(next_q)
    elif is_quiz_complete(user_sessions[email]):
        return jsonify({"complete": True})
    else:
        return jsonify({"status": "loading"}), 202

# 최종 결과 요청
@app.route("/api/result", methods=["GET"])
def get_result():
    email = request.args.get("email")
    if email not in user_sessions:
        return jsonify({"error": "세션이 없습니다."}), 400

    result = get_user_result_summary(user_sessions[email])
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
