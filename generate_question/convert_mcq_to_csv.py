import json
import pandas as pd
import csv

def convert_mcq_json_to_csv(input_file, output_file):
    """
    MCQ JSON 파일을 CSV로 변환합니다.

    Args:
        input_file (str): 입력 JSON 파일 경로
        output_file (str): 출력 CSV 파일 경로
    """

    # JSON 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # CSV 데이터 준비
    csv_data = []

    for item in data:
        drug_idx = item[0]  # 첫 번째 요소는 drug_idx
        question = item[1]  # 두 번째 요소는 question
        answer = item[2]    # 세 번째 요소는 answer

        # CSV 행 추가 (question_type, drug_idx, question, answer 순서)
        csv_data.append(['mcq', drug_idx, question, answer])

    # CSV 파일로 저장 (UTF-8 인코딩)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # 헤더 작성
        writer.writerow(['question_type', 'drug_idx', 'question', 'answer'])

        # 데이터 작성
        writer.writerows(csv_data)

    print(f"변환 완료: {len(csv_data)}개의 문제가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    # 파일 경로 설정
    input_file = "medqa/MCQ/test.json"
    output_file = "medqa/MCQ/test.csv"

    # 변환 실행
    convert_mcq_json_to_csv(input_file, output_file)
