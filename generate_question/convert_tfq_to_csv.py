import json
import pandas as pd
import csv

def convert_tfq_json_to_csv(input_file, output_file):
    """
    TFQ JSON 파일을 CSV로 변환합니다.

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
        question1 = item[1]  # 두 번째 요소는 문제1
        question2 = item[2]  # 세 번째 요소는 문제2
        question3 = item[3]  # 네 번째 요소는 문제3
        question4 = item[4]  # 다섯 번째 요소는 문제4
        answer1 = item[5]    # 여섯 번째 요소는 정답1 (T/F)
        answer2 = item[6]    # 일곱 번째 요소는 정답2 (T/F)
        answer3 = item[7]    # 여덟 번째 요소는 정답3 (T/F)
        answer4 = item[8]    # 아홉 번째 요소는 정답4 (T/F)

        # 첫 번째 문제 처리
        answer_text1 = "True" if answer1 == "T" else "False"
        csv_data.append(['tfq_1', drug_idx, question1, answer_text1])

        # 두 번째 문제 처리
        answer_text2 = "True" if answer2 == "T" else "False"
        csv_data.append(['tfq_1', drug_idx, question2, answer_text2])

        # 세 번째 문제 처리
        answer_text3 = "True" if answer3 == "T" else "False"
        csv_data.append(['tfq_1', drug_idx, question3, answer_text3])

        # 네 번째 문제 처리
        answer_text4 = "True" if answer4 == "T" else "False"
        csv_data.append(['tfq_1', drug_idx, question4, answer_text4])

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
    input_file = "medqa/TFQ/test.json"
    output_file = "medqa/TFQ/test.csv"

    # 변환 실행
    convert_tfq_json_to_csv(input_file, output_file)
