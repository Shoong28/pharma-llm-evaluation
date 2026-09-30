import json
from pathlib import Path

# 입력과 출력 파일 경로
input_path = Path('문항생성/atc_N_filtered.jsonl')
output_path = Path('문항생성/filtered_five_or_more_N.jsonl')

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

count_written = 0
with input_path.open('r', encoding='utf-8') as fin, \
     output_path.open('w', encoding='utf-8') as fout:
    for line in fin:
        data = json.loads(line)
        present_count = sum(1 for field in fields_to_check if data.get(field))
        if present_count >= 5:
            # JSON 객체를 다시 문자열로 변환하여 한 줄로 씁니다.
            fout.write(json.dumps(data, ensure_ascii=False) + '\n')
            count_written += 1

print(f'Saved {count_written} drug entries with at least five non-missing fields to {output_path}')
