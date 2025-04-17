from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gpt_eval_api_flow import (
    generate_next_step,
    load_step_context,
    generate_next_question,
    user_sessions
)
from gpt_function_schema import functions
import openai
import os
import json

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

client = openai.OpenAI()

# ✅ 1. 사용자 초기화
@app.route("/api/start", methods=["POST"])
def start_quiz():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"error": "이메일이 제공되지 않았습니다."}), 400

        user_sessions[email] = {
            "step_sequence": [],
            "history": [],
            "current_index": 0,
        }
        return jsonify({"status": "initialized"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ 2. 다음 문제 요청
@app.route("/api/next-question", methods=["GET"])
def next_question():
    try:
        email = request.args.get("email")
        current_index = int(request.args.get("index", 0))

        step = generate_next_step(email, current_index)
        if step is None:
            return jsonify({"complete": True})

        context = load_step_context(step)
        if context is None:
            return jsonify({"error": f"Context for {step} not found"})

        prompt = f"""다음은 {step} 단계의 학습 콘텐츠입니다. 이를 바탕으로 실무 적용 중심의 심화 서술형 문제를 1문항 생성해 주세요.
조건:
- 학습자의 실무 적용 능력을 평가할 수 있도록 실제 사례 기반 질문으로 구성
- 콘텐츠 이해도를 파악할 수 있도록 비판적 사고를 유도
- 문제는 한국어로 제공"""

        question = generate_next_question(prompt, context)
        if question is None:
            return jsonify({"error": "문제 생성 실패"})

        return jsonify({
            "step": step,
            "question": question,
            "context": context,
            "complete": False
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ 3. 답안 제출 및 평가
@app.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    try:
        data = request.get_json()
        email = data.get("email")
        user_answer = data.get("answer")
        current_index = data.get("index", 0)

        step = generate_next_step(email, current_index)
        context = load_step_context(step)

        if step is None or context is None:
            return jsonify({"complete": False, "feedback": {"error": "문제 평가 정보 누락"}})

        messages = [
            {
                "role": "system",
                "content": f"{step} 문항 채점 기준에 따라 다음 답안을 평가하세요. 기준: 이해도, 실무 적용 가능성, 구체성."
            },
            {"role": "user", "content": f"📘 문맥: {context}\n\n✍️ 학습자 답변: {user_answer}"}
        ]

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.5,
            functions=functions,
            function_call={"name": "evaluate_answer"},
        )

        function_args = response.choices[0].message.function_call.arguments
        feedback = json.loads(function_args)

        complete = (current_index + 1 >= 30)

        return jsonify({
            "complete": complete,
            "feedback": {
                "answer": user_answer,
                "question": data.get("question", ""),
                "step": step,
                **feedback,
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ 4. 정적 HTML 서빙
@app.route("/")
def root():
    return send_from_directory(app.static_folder, "quiz_ui_web.html")

# ✅ 5. 포트 감지 (Render 환경)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
