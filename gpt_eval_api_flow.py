import random
import json
import openai
from openai import OpenAI

client = OpenAI()

# 사용자별 상태 저장
user_sessions = {}

def initialize_step_sequence():
    step_labels = [f"STEP {i}" for i in range(1, 10)]
    sequence = []
    while len(sequence) < 30:
        random.shuffle(step_labels)
        sequence.extend(step_labels)
    return sequence[:30]

# ✅ 사용자 초기화
def init_user_session(name, email):
    user_sessions[email] = {
        "name": name,
        "email": email,
        "step_sequence": initialize_step_sequence(),
        "current_index": 0,
        "answers": []
    }

# ✅ 다음 STEP 반환
def generate_next_step(email, current_index):
    if email not in user_sessions:
        return None
    sequence = user_sessions[email]["step_sequence"]
    if current_index >= len(sequence):
        return None
    return sequence[current_index]

# ✅ STEP별 JSON context 로딩
def load_step_context(step_label):
    filename = f"{step_label.lower().replace(' ', '_')}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["context"]
    except Exception:
        return None

# ✅ 문제 생성
def generate_next_question(prompt_template, context):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception:
        return None

# ✅ 답변 평가 함수 (Function Calling 기반)
def evaluate_answer(answer, context=None, step="STEP ?"):
    prompt = f"""
다음은 WiseCollector 학습자가 작성한 답변입니다. 아래 기준에 따라 평가해주세요:
- 답변의 정확성
- 실무 적용 가능성
- 서술의 구체성
- 학습 내용의 반영 여부

문항 STEP: {step}
"""
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"📝 학습자 답변: {answer}"}
        ]

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.5,
            functions=[
                {
                    "name": "evaluate_answer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "feedback": {"type": "string"},
                            "recommendation": {"type": "string"},
                            "level": {
                                "type": "string",
                                "enum": ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
                            }
                        },
                        "required": ["score", "feedback", "recommendation", "level"]
                    }
                }
            ],
            function_call={"name": "evaluate_answer"}
        )

        args = response.choices[0].message.function_call.arguments
        return json.loads(args)

    except Exception as e:
        return {"error": str(e)}

# ✅ 진단 결과 리포트 생성 (임시)
def generate_report():
    return {
        "message": "진단 리포트 기능은 아직 구현되지 않았습니다."
    }

# ✅ 빠졌던 핵심 함수: 현재 문제 반환
def get_next_question():
    try:
        # 테스트용 기본 사용자 이메일 (실제 서비스 시 세션으로 받아야 함)
        email = next(iter(user_sessions))
        user = user_sessions[email]
        index = user["current_index"]
        step = user["step_sequence"][index]
        context = load_step_context(step)

        prompt = f"{step}의 학습 내용을 바탕으로 실무형 문제를 1문항 생성하세요."
        question = generate_next_question(prompt, context)

        # 상태 갱신
        user["current_index"] += 1
        user["answers"].append({"step": step, "question": question})

        return {
            "step": step,
            "question": question,
            "number": index + 1,
            "total": 30
        }

    except Exception as e:
        return {"error": str(e)}
