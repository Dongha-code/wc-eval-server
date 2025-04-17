quiz_function_definitions = [
  {
    "name": "generate_quiz_question",
    "description": "사용자에게 출제할 WiseCollector 2.0 기반 진단용 문제 1개를 생성한다.",
    "parameters": {
      "type": "object",
      "properties": {
        "step": {
          "type": "string",
          "description": "문제를 생성할 대상 STEP (예: 'STEP 1', 'STEP 2' 등)"
        },
        "context": {
          "type": "string",
          "description": "해당 STEP의 전체 학습 콘텐츠 내용"
        },
        "question": {
          "type": "string",
          "description": "실제로 사용자에게 제시할 실무형 문제 내용"
        }
      },
      "required": ["step", "context", "question"]
    }
  },
  {
    "name": "submit_answer",
    "description": "사용자가 제출한 답변을 평가하고 피드백을 제공한다.",
    "parameters": {
      "type": "object",
      "properties": {
        "question": { "type": "string", "description": "문제 내용" },
        "answer": { "type": "string", "description": "사용자의 답변" },
        "step": { "type": "string", "description": "소속된 STEP 번호" },
        "correct": { "type": "string", "description": "모범 답안 (있을 경우)" }
      },
      "required": ["question", "answer", "step"]
    }
  },
  {
    "name": "generate_diagnostic_report",
    "description": "전체 응답 기반 진단 리포트를 생성한다.",
    "parameters": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "email": { "type": "string" },
        "date": { "type": "string" },
        "summary": {
          "type": "object",
          "properties": {
            "정답률": { "type": "number" },
            "STEP1": { "type": "number" }, "STEP2": { "type": "number" }, "STEP3": { "type": "number" },
            "STEP4": { "type": "number" }, "STEP5": { "type": "number" }, "STEP6": { "type": "number" },
            "STEP7": { "type": "number" }, "STEP8": { "type": "number" }, "STEP9": { "type": "number" },
            "추천STEP": { "type": "string" },
            "강점요약": { "type": "string" },
            "약점요약": { "type": "string" },
            "전체평가요약": { "type": "string" },
            "레벨": { "type": "string" }
          },
          "required": ["정답률", "레벨"]
        }
      },
      "required": ["name", "email", "date", "summary"]
    }
  }
]