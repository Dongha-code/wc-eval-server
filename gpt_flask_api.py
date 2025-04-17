import json
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from gpt_function_schema import quiz_function_definitions

# ✅ 로그 설정
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_context_for_step(step: str) -> str:
    filename = f"step_{step.split()[-1]}.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["context"]

def generate_question(step: str):
    try:
        context = load_context_for_step(step)
        log.info(f"\n📘 [STEP]: {step}")
        log.info(f"📄 [CONTEXT 길이]: {len(context)}")

        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ 변경 완료
            messages=[
                {"role": "system", "content": "너는 WiseCollector 2.0 진단 문제 출제자야."},
                {"role": "user", "content": f"{step} 내용 기반 실무형 문제를 생성해줘:\n\n{context}"}
            ],
            functions=quiz_function_definitions,
            function_call={"name": "generate_quiz_question"},
            timeout=20
        )

        message = response.choices[0].message
        log.info(f"📨 [GPT 응답 role]: {message.role}")
        log.info(f"📨 [GPT function_call]: {message.function_call}")

        call = message.function_call
        if not call or not call.arguments:
            raise ValueError("GPT가 function_call 또는 arguments를 반환하지 않았습니다.")

        result = json.loads(call.arguments)
        if not result.get("question"):
            raise ValueError("GPT 응답에 question 필드가 없습니다.")

        return result

    except Exception as e:
        log.error(f"❌ 문제 생성 실패 ({step}): {e}")
        return {
            "question": f"❌ 문제 생성 실패: {str(e)}",
            "choices": [],
            "step": step
        }

def evaluate_answer(question: str, answer: str, step: str, correct=""):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ 변경 완료
            messages=[
                {"role": "system", "content": "넌 교육 평가자야. 사용자 응답을 평가하고 피드백을 줘."},
                {"role": "user", "content": f"문제: {question}\n답변: {answer}\n모범 답안: {correct}"}
            ],
            functions=quiz_function_definitions,
            function_call={"name": "submit_answer"},
            timeout=20
        )
        return json.loads(response.choices[0].message.function_call.arguments)
    except Exception as e:
        log.error(f"❌ 답안 평가 실패 ({step}): {e}")
        return {"feedback": f"❌ 평가 실패: {str(e)}", "step": step}

def generate_report(name: str, email: str, answers: list):
    try:
        messages = [
            {"role": "system", "content": "넌 진단 결과 리포트를 생성하는 GPT야."},
            {"role": "user", "content": f"다음은 {name}({email})의 진단 응답이야. 요약해줘.\n\n{json.dumps(answers, ensure_ascii=False)}"}
        ]
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ 변경 완료
            messages=messages,
            functions=quiz_function_definitions,
            function_call={"name": "generate_diagnostic_report"},
            temperature=0.7,
            timeout=20
        )
        return json.loads(response.choices[0].message.function_call.arguments)
    except Exception as e:
        log.error("❌ 리포트 생성 실패:", e)
        return {"report": f"❌ 리포트 생성 실패: {str(e)}"}
