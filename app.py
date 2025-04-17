from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from gpt_eval_api_flow import (
    init_user_session,
    get_next_question,
    evaluate_answer,
    is_quiz_complete,
    generate_report
)

app = Flask(__name__, static_url_path='/static')
CORS(app)

@app.route('/')
def root():
    return redirect("/static/quiz_ui_web.html")

@app.route('/api/start', methods=['POST'])
def start_quiz():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    init_user_session(name, email)
    return jsonify({"message": "Started"}), 200

@app.route('/api/next-question', methods=['GET'])
def next_question():
    q = get_next_question()
    return jsonify(q)

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    answer = data.get("answer")
    try:
        result = evaluate_answer(answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/report', methods=['GET'])
def report():
    result = generate_report()
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
