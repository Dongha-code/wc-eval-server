# GPT 기반 자동 평가 대화 흐름 (Flask API 연동 포함)

from openai import OpenAI
from dotenv import load_dotenv
import os, requests, json
from datetime import datetime

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK")  # 시트 저장용 웹훅 주소

# STEP별 콘텐츠 불러오기 (사전 로딩)
step_contexts = {}
for i in range(1, 10):
    with open(f"step_{i}.json", "r", encoding="utf-8") as f:
        step_data = json.load(f)
        step_contexts[f"STEP {i}"] = step_data

# 사용자 진행 세션 초기화
session = {
    "name": None,
    "email": None,
    "current": 0,
    "responses": [],
    "questions": []
}

def generate_next_question():
    step_num = (session["current"] % 9) + 1
    step_id = f"STEP {step_num}"
    context = step_contexts[step_id]["context"]

    response = client.chat.completions.create(
        model="gpt-4-turbo",  # ✅ 변경 완료
        messages=[
            {"role": "system", "content": "너는 WiseCollector 진단 문제 출제자야. 반드시 한국어로 문제를 만들어야 해."},
            {"role": "user", "content": context}
        ],
        functions=[{
            "name": "generate_quiz_question",
            "parameters": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "context": {"type": "string"}
                },
                "required": ["step", "context"]
            }
        }],
        function_call={"name": "generate_quiz_question"}
    )

    args = json.loads(response.choices[0].message.function_call.arguments)
    question = {
        "step": step_id,
        "question": f"{step_id}: {args['context'][:80]}... 에 기반한 문제를 생성하세요."
    }
    session["questions"].append(question)
    return question

def submit_user_answer(user_answer):
    current_q = session["questions"][session["current"]]

    response = client.chat.completions.create(
        model="gpt-4-turbo",  # ✅ 변경 완료
        messages=[
            {"role": "system", "content": "넌 GPT 평가자야. 반드시 한국어로 피드백을 줘."},
            {"role": "user", "content": f"문제: {current_q['question']}\n답변: {user_answer}"}
        ],
        functions=[{
            "name": "submit_answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "step": {"type": "string"}
                },
                "required": ["question", "answer", "step"]
            }
        }],
        function_call={"name": "submit_answer"}
    )

    feedback = json.loads(response.choices[0].message.function_call.arguments)
    session["responses"].append({"question": current_q["question"], "answer": user_answer, "feedback": feedback})
    session["current"] += 1
    return feedback

def generate_final_report():
    today = datetime.today().strftime("%Y-%m-%d")

    # 샘플 정답률 계산 (임시)
    score = 70 + (session["current"] % 30)
    summary = {
        "이름": session["name"],
        "이메일": session["email"],
        "진단일": today,
        "레벨": "Level 3",
        "정답률": score,
        "STEP1": 85, "STEP2": 70, "STEP3": 60,
        "STEP4": 80, "STEP5": 75, "STEP6": 90,
        "STEP7": 78, "STEP8": 65, "STEP9": 85,
        "추천STEP": "STEP3, STEP8",
        "강점요약": "태깅 구조 이해, 변수 활용 능숙",
        "약점요약": "보안 설정 미흡, 성능 항목 취약",
        "전체평가요약": "실무 이해는 양호하나 일부 STEP은 추가 학습 필요"
    }

    # 전송
    res = requests.post(WEBHOOK_URL, json=summary)
    return summary if res.ok else {"error": res.text}
