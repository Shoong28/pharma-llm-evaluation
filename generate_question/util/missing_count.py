import json
from pathlib import Path

# 분석할 JSONL 파일 경로
filtered_path = Path('문항생성/atc_N_filtered.jsonl')

# 체크할 필드 목록 (name 제외)
fields_to_check = [
    'description',
    'mechanism_of_action',
    'pharmacodynamics',
    'indication',
    'classification',
    'affected_organisms',
    'toxicity'
]

count_with_five_or_more = 0
matching_names = []

with filtered_path.open('r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # 현재 약물에서 값이 존재하는 필드 개수 계산
        present_count = sum(1 for field in fields_to_check if data.get(field))
        if present_count >= 5: # 5개 이상의 필드가 존재하는 약물
            count_with_five_or_more += 1
            matching_names.append(data.get('name', 'N/A'))

print(f'Number of drugs with at least five non-missing fields (excluding name): {count_with_five_or_more}')
# 필요하다면 해당 약물들의 이름을 확인할 수도 있습니다.
# print(matching_names)
