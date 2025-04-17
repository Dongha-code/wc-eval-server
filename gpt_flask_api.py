from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function Definitions (이미 정의된 quiz_function_definitions를 import 했다고 가정)
from gpt_function_schema import quiz_function_definitions

@app.route("/generate-question", methods=["POST"])
def generate_question():
    data = request.json
    step = data.get("step")
    context = data.get("context")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 WiseCollector 2.0 진단 문제 출제자야."},
            {"role": "user", "content": f"다음 STEP 내용을 기반으로 실무형 문제를 만들어줘.\n\n{context}"}
        ],
        functions=quiz_function_definitions,
        function_call={"name": "generate_quiz_question"}
    )

    function_args = response.choices[0].message.function_call.arguments
    return jsonify({"generated": function_args})


@app.route("/evaluate", methods=["POST"])
def evaluate_answer():
    data = request.json
    question = data.get("question")
    answer = data.get("answer")
    step = data.get("step")
    correct = data.get("correct") or ""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "넌 교육 평가자야. 사용자 응답을 평가하고 피드백을 줘."},
            {"role": "user", "content": f"문제: {question}\n답변: {answer}\n모범 답안: {correct}"}
        ],
        functions=quiz_function_definitions,
        function_call={"name": "submit_answer"}
    )

    function_args = response.choices[0].message.function_call.arguments
    return jsonify({"evaluation": function_args})


@app.route("/report", methods=["POST"])
def generate_report():
    data = request.json

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "넌 진단 결과 리포트를 생성하는 GPT야."},
            {"role": "user", "content": "응답 데이터를 기반으로 진단 요약표를 만들어줘."}
        ],
        functions=quiz_function_definitions,
        function_call={"name": "generate_diagnostic_report"},
        temperature=0.7
    )

    function_args = response.choices[0].message.function_call.arguments
    return jsonify({"report": function_args})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
