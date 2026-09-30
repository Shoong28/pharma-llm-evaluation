import pandas as pd
import os
from pathlib import Path

# 폴더 경로 설정
folder_30 = Path('30')
folder_70 = Path('70')
output_folder = Path('100(merged)')

# 출력 폴더가 없으면 생성
output_folder.mkdir(exist_ok=True)

# 문항 유형별 기본키 정의
primary_keys = {
    'MCQ': ['idx'],
    'MAQ': ['idx', 'n_or_p'],
    'RQ': ['idx', 'T_or_F'],
    'TFQ': ['idx', 'n_or_p', 'T_or_F']
}

def clean_idx(df):
    """idx 컬럼값에 _가 있을 경우, _ 앞의 값만 남김"""
    if 'idx' in df.columns:
        df['idx'] = df['idx'].astype(str).str.split('_').str[0]
    return df

def get_question_type(filename):
    """파일명에서 문항 유형 추출"""
    for q_type in ['MCQ', 'MAQ', 'RQ', 'TFQ']:
        if q_type in filename:
            return q_type
    return None

def reorder_columns(df, q_type):
    """컬럼 순서 재정렬: 기본키, ques, label 순서로, 나머지는 맨 뒤"""
    pkeys = primary_keys.get(q_type, ['idx'])

    # 존재하는 컬럼만 사용
    existing_pkeys = [k for k in pkeys if k in df.columns]

    # 기본 순서: 기본키 -> ques -> label
    ordered_cols = existing_pkeys.copy()

    if 'ques' in df.columns:
        ordered_cols.append('ques')
    if 'label' in df.columns:
        ordered_cols.append('label')

    # 나머지 컬럼들 추가
    remaining_cols = [col for col in df.columns if col not in ordered_cols]
    ordered_cols.extend(remaining_cols)

    return df[ordered_cols]

def sort_rows(df, q_type):
    """행 정렬: idx를 기준으로, idx 동일하면 기본키 순서로 정렬"""
    pkeys = primary_keys.get(q_type, ['idx'])

    # 존재하는 컬럼만 사용
    existing_pkeys = [k for k in pkeys if k in df.columns]

    if existing_pkeys:
        # idx는 숫자로 변환하여 정렬
        if 'idx' in df.columns:
            df['idx'] = pd.to_numeric(df['idx'], errors='coerce')

        df = df.sort_values(by=existing_pkeys).reset_index(drop=True)

    return df

def merge_and_process(filename):
    """파일 병합 및 정제 처리"""
    print(f"\n처리 중: {filename}")

    # 파일 읽기
    file_30 = folder_30 / filename
    file_70 = folder_70 / filename

    if not file_30.exists() or not file_70.exists():
        print(f"  경고: {filename} 파일이 두 폴더 중 하나에 없습니다.")
        return

    df_30 = pd.read_excel(file_30)
    df_70 = pd.read_excel(file_70)

    print(f"  - 30 폴더: {len(df_30)}행")
    print(f"  - 70 폴더: {len(df_70)}행")

    # 병합
    df_merged = pd.concat([df_30, df_70], ignore_index=True)
    print(f"  - 병합 후: {len(df_merged)}행")

    # 문항 유형 추출
    q_type = get_question_type(filename)
    if not q_type:
        print(f"  경고: 문항 유형을 파악할 수 없습니다: {filename}")
        q_type = 'MCQ'  # 기본값

    print(f"  - 문항 유형: {q_type}")

    # 1. idx 정제
    df_merged = clean_idx(df_merged)
    print(f"  - idx 정제 완료")

    # 2. 컬럼 순서 재정렬
    df_merged = reorder_columns(df_merged, q_type)
    print(f"  - 컬럼 순서 재정렬 완료")

    # 3. 행 정렬
    df_merged = sort_rows(df_merged, q_type)
    print(f"  - 행 정렬 완료")

    # 저장
    output_path = output_folder / filename
    df_merged.to_excel(output_path, index=False)
    print(f"  - 저장 완료: {output_path}")
    print(f"  - 최종 행 수: {len(df_merged)}")

# 메인 처리
if __name__ == "__main__":
    print("=" * 60)
    print("파일 병합 및 정제 시작")
    print("=" * 60)

    # 30 폴더의 파일 목록 가져오기
    files_to_merge = [f.name for f in folder_30.glob('*.xlsx')]

    if not files_to_merge:
        print("처리할 파일이 없습니다.")
    else:
        print(f"\n총 {len(files_to_merge)}개 파일 처리 예정:")
        for f in files_to_merge:
            print(f"  - {f}")

        # 각 파일 처리
        for filename in files_to_merge:
            merge_and_process(filename)

        print("\n" + "=" * 60)
        print("모든 파일 병합 및 정제 완료!")
        print("=" * 60)
