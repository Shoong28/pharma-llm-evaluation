import csv
import json
from collections import defaultdict
import os

def parse_umls_data():
    """
    UMLS MRCONSO.RRF 파일을 파싱해서 concept_attributes.json 생성
    """
    concept_synonyms = defaultdict(set)

    # MRCONSO.RRF 파일 경로 (UMLS에서 다운로드한 파일)
    mrconso_path = 'MRCONSO.RRF'

    # 파일 존재 여부 확인
    if not os.path.exists(mrconso_path):
        print(f"파일을 찾을 수 없습니다: {mrconso_path}")
        print(f"현재 작업 디렉토리: {os.getcwd()}")
        print(f"현재 디렉토리의 파일들:")
        for file in os.listdir('.'):
            if 'MRCONSO' in file or 'mrconso' in file:
                print(f"  - {file}")
        return None

    print(f"파일을 찾았습니다: {mrconso_path}")
    print(f"파일 크기: {os.path.getsize(mrconso_path)} bytes")

    # 다양한 인코딩으로 시도
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            print(f"인코딩 {encoding}으로 시도 중...")

            with open(mrconso_path, 'r', encoding=encoding) as f:
                line_count = 0
                for line in f:
                    line_count += 1

                    # 처음 몇 줄 출력해서 구조 확인
                    if line_count <= 3:
                        print(f"Line {line_count}: {line.strip()}")

                    # RRF 파일은 |로 구분된 필드
                    fields = line.strip().split('|')

                    # MRCONSO.RRF는 19개 필드를 가짐
                    if len(fields) >= 19:
                        cui = fields[0]  # Concept Unique Identifier
                        language = fields[1]  # Language
                        term_status = fields[2]  # Term Status
                        string_type = fields[4]  # String Type (PF = Preferred Form)
                        string = fields[14]  # String (의학 용어) - 올바른 필드!

                        # 영어이고 유효한 상태의 용어만 포함
                        if (language == 'ENG' and
                            term_status == 'P' and  # Preferred term
                            string_type == 'PF' and  # Preferred form
                            string.strip()):

                            concept_synonyms[cui].add(string.strip())

                    # 진행 상황 표시
                    if line_count % 100000 == 0:
                        print(f"처리된 줄 수: {line_count:,}")

                print(f"총 {line_count:,}줄을 처리했습니다.")
                break

        except UnicodeDecodeError:
            print(f"인코딩 {encoding} 실패, 다음 인코딩 시도...")
            continue
        except Exception as e:
            print(f"오류 발생: {e}")
            continue

    # 딕셔너리를 리스트로 변환 (JSON 직렬화를 위해)
    concept_attributes = {}
    for cui, synonyms in concept_synonyms.items():
        concept_attributes[cui] = list(synonyms)

    print(f"총 {len(concept_attributes)}개의 개념을 찾았습니다.")

    return concept_attributes

def save_concept_attributes(concept_attributes, output_file='concept_attributes.json'):
    """
    concept_attributes를 JSON 파일로 저장
    """
    if concept_attributes:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(concept_attributes, f, indent=2, ensure_ascii=False)
        print(f"{output_file} 파일이 생성되었습니다.")
        print(f"총 {len(concept_attributes)}개의 개념이 포함되었습니다.")

        # 샘플 데이터 출력
        print("\n샘플 데이터:")
        sample_items = list(concept_attributes.items())[:5]
        for cui, synonyms in sample_items:
            print(f"  {cui}: {synonyms[:3]}...")
    else:
        print("concept_attributes를 생성할 수 없습니다.")

if __name__ == "__main__":
    print("UMLS 데이터 파싱을 시작합니다...")
    concept_attributes = parse_umls_data()
    save_concept_attributes(concept_attributes)
