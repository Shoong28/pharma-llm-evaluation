import json
import pandas as pd
import csv

def convert_rq_json_to_csv(input_file, output_file):
    """
    RQ JSON 파일을 CSV로 변환합니다.

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
        question1 = item[1]  # 두 번째 요소는 문제1-1
        question2 = item[2]  # 세 번째 요소는 문제1-2
        answer1 = item[3]    # 네 번째 요소는 정답1-1 [T/F, A/B/C/D]
        answer2 = item[4]    # 다섯 번째 요소는 정답1-2 [T/F, A/B/C/D]

        # 첫 번째 문제 처리
        tf1 = "True" if answer1[0] == "T" else "False"
        option1 = answer1[1]
        answer_text1 = f"{tf1}, {option1}"
        csv_data.append(['rq', drug_idx, question1, answer_text1])

        # 두 번째 문제 처리
        tf2 = "True" if answer2[0] == "T" else "False"
        option2 = answer2[1]
        answer_text2 = f"{tf2}, {option2}"
        csv_data.append(['rq', drug_idx, question2, answer_text2])

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
    input_file = "medqa/RQ/test.json"
    output_file = "medqa/RQ/test.csv"

    # 변환 실행
    convert_rq_json_to_csv(input_file, output_file)
