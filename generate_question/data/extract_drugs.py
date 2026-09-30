import json
import os
import re

def process_drug_data(input_file, output_dir, top_n=50):
    """
    JSONL 파일을 읽어 정보량이 많은 순서대로 상위 N개를 추출하여 개별 파일로 저장합니다.
    """

    # 1. 데이터 로드
    data_list = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # 빈 줄 방지
                    data_list.append(json.loads(line))
    except FileNotFoundError:
        print(f"오류: '{input_file}' 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(data_list)}개의 약물 데이터를 불러왔습니다.")

    # 2. 정보량(결측값이 아닌 필드의 수) 계산 함수
    def count_valid_fields(item):
        count = 0
        for value in item.values():
            # None이 아니고, 빈 문자열이나 빈 리스트가 아닌 경우 정보가 있다고 판단
            if value is not None and value != "" and value != []:
                count += 1
        return count

    # 3. 정보량이 많은 순서대로 정렬 (내림차순)
    # key에 함수를 적용하여 그 결과를 기준으로 정렬합니다.
    sorted_data = sorted(data_list, key=count_valid_fields, reverse=True)

    # 4. 상위 N개 추출
    top_drugs = sorted_data[:top_n]
    print(f"정보량이 가장 많은 상위 {len(top_drugs)}개를 선별했습니다.")

    # 저장할 디렉토리 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 5. 개별 파일로 저장
    saved_count = 0
    for drug in top_drugs:
        drug_name = drug.get('name', 'Unknown_Drug')

        # 파일명에 사용할 수 없는 특수문자 제거 (Windows/Linux 파일시스템 호환)
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", drug_name)
        file_path = os.path.join(output_dir, f"{safe_filename}.txt")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 텍스트 파일에 보기 좋게 저장 (JSON 형식을 유지하되 들여쓰기 적용)
                # ensure_ascii=False를 해야 한글이나 특수문자가 깨지지 않고 저장됩니다.
                json.dump(drug, f, indent=4, ensure_ascii=False)
            saved_count += 1
        except Exception as e:
            print(f"'{drug_name}' 저장 중 오류 발생: {e}")

    print(f"\n완료! '{output_dir}' 폴더에 총 {saved_count}개의 파일이 저장되었습니다.")

# 실행 설정
if __name__ == "__main__":
    # 입력 파일명 (업로드하신 파일명)
    INPUT_FILENAME = 'filtered_five_or_more_N.jsonl'

    # 결과물이 저장될 폴더명
    OUTPUT_FOLDER = 'top_50_drugs'

    process_drug_data(INPUT_FILENAME, OUTPUT_FOLDER)
