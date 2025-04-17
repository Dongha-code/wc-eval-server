import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from gpt_function_schema import quiz_function_definitions

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_context_for_step(step: str) -> str:
    filename = f"step_{step.split()[-1]}.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["context"]

def generate_question(step: str):
    context = load_context_for_step(step)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 WiseCollector 2.0 진단 문제 출제자야."},
            {"role": "user", "content": f"다음 STEP 내용을 기반으로 실무형 문제를 만들어줘.\n\n{context}"}
        ],
        functions=quiz_function_definitions,
        function_call={"name": "generate_quiz_question"}
    )
    return json.loads(response.choices[0].message.function_call.arguments)

def evaluate_answer(question: str, answer: str, step: str, correct=""):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "넌 교육 평가자야. 사용자 응답을 평가하고 피드백을 줘."},
            {"role": "user", "content": f"문제: {question}\n답변: {answer}\n모범 답안: {correct}"}
        ],
        functions=quiz_function_definitions,
        function_call={"name": "submit_answer"}
    )
    return json.loads(response.choices[0].message.function_call.arguments)

def generate_report(name: str, email: str, answers: list):
    messages = [
        {"role": "system", "content": "넌 진단 결과 리포트를 생성하는 GPT야."},
        {"role": "user", "content": f"다음은 {name}({email})의 진단 응답이야. 요약해줘.\n\n{json.dumps(answers, ensure_ascii=False)}"}
    ]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        functions=quiz_function_definitions,
        function_call={"name": "generate_diagnostic_report"},
        temperature=0.7
    )
    return json.loads(response.choices[0].message.function_call.arguments)
