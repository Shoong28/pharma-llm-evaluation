import json
import pandas as pd
from pathlib import Path

def convert_mcqs_jsonl_to_excel(input_jsonl: str, output_excel: str) -> None:
    """
    JSONL 형식의 약물 MCQ 데이터에서 질문 정보만 추출해 엑셀로 저장합니다.
    """
    records = []
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            drug_name = entry.get('drug_name')
            # 각 질문을 별도의 행으로 처리
            for q in entry.get('questions', []):
                records.append({
                    'drug_name': drug_name,
                    'question': q.get('question'),
                    'option_A': q.get('option_A'),
                    'option_B': q.get('option_B'),
                    'option_C': q.get('option_C'),
                    'option_D': q.get('option_D'),
                    'answers': q.get('answers')  # A/B/C/D 형식, 여러 정답은 슬래시(/)로 구분
                })

    # DataFrame 생성 후 엑셀로 저장
    df = pd.DataFrame(records)
    df.to_excel(output_excel, index=False)
    print(f'Converted {len(records)} questions to {output_excel}')

# 사용 예시
convert_mcqs_jsonl_to_excel('문항생성/all_mcqs.jsonl', '문항생성/all_mcqs.xlsx')
