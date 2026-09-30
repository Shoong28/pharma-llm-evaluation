#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WHO ATC-DDD 데이터 분석 스크립트
"""

import pandas as pd
import re
import logging
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_who_atc_data(file_path):
    """
    WHO ATC-DDD 데이터 분석
    """
    logger.info(f"WHO ATC-DDD 데이터 분석 시작: {file_path}")

    # CSV 파일 읽기
    df = pd.read_csv(file_path)

    logger.info(f"총 행 수: {len(df)}")
    logger.info(f"컬럼: {list(df.columns)}")

    # 컬럼 정보 확인
    logger.info("\n=== 컬럼 정보 ===")
    for col in df.columns:
        logger.info(f"{col}: {df[col].dtype}")

    # ATC 코드 길이별 분류
    def get_atc_level(atc_code):
        """ATC 코드의 단계를 반환"""
        if pd.isna(atc_code) or atc_code == 'NA':
            return 'NA'

        code = str(atc_code).strip()
        if len(code) == 1:
            return 'Level 1 (Anatomical)'
        elif len(code) == 3:
            return 'Level 2 (Therapeutic)'
        elif len(code) == 4:
            return 'Level 3 (Pharmacological)'
        elif len(code) == 5:
            return 'Level 4 (Chemical)'
        elif len(code) == 7:
            return 'Level 5 (Substance)'
        else:
            return 'Other'

    # ATC 코드 단계별 분류
    df['atc_level'] = df['atc_code'].apply(get_atc_level)

    # 단계별 통계
    level_stats = df['atc_level'].value_counts()

    logger.info("\n=== ATC 코드 단계별 분포 ===")
    for level, count in level_stats.items():
        logger.info(f"{level}: {count}개")

    # 실제 의약품 (Level 5)만 필터링
    actual_drugs = df[df['atc_level'] == 'Level 5 (Substance)']

    logger.info(f"\n=== 실제 의약품 (Level 5) ===")
    logger.info(f"총 의약품 수: {len(actual_drugs)}개")

    # ATC 1단계별 의약품 분포
    def get_first_level(atc_code):
        """ATC 코드의 1단계 추출"""
        if pd.isna(atc_code) or atc_code == 'NA':
            return 'NA'

        code = str(atc_code).strip()
        if len(code) >= 1:
            return code[0]
        return 'NA'

    actual_drugs['first_level'] = actual_drugs['atc_code'].astype(str).apply(get_first_level)
    first_level_stats = actual_drugs['first_level'].value_counts()

    logger.info(f"\n=== ATC 1단계별 의약품 분포 ===")
    atc_names = {
        'A': '소화관 및 대사 (Alimentary tract and metabolism)',
        'B': '혈액 및 조혈기관 (Blood and blood forming organs)',
        'C': '심혈관계 (Cardiovascular system)',
        'D': '피부용 (Dermatologicals)',
        'G': '생식비뇨계 및 성호르몬 (Genito urinary system and sex hormones)',
        'H': '전신성 호르몬제 (Systemic hormonal preparations)',
        'J': '감염증 치료용 항미생물제 (Antiinfectives for systemic use)',
        'L': '항종양제 및 면역조절제 (Antineoplastic and immunomodulating agents)',
        'M': '근골격계 (Musculo-skeletal system)',
        'N': '신경계 (Nervous system)',
        'P': '항기생충제, 살충제 및 기생충 방제제 (Antiparasitic products, insecticides and repellents)',
        'R': '호흡계 (Respiratory system)',
        'S': '감각기관 (Sensory organs)',
        'V': '기타 (Various)'
    }

    for level, count in sorted(first_level_stats.items()):
        if level in atc_names:
            logger.info(f"{level} ({atc_names[level]}): {count}개")
        else:
            logger.info(f"{level}: {count}개")

    # DDD 정보가 있는 의약품 확인
    ddd_drugs = actual_drugs[actual_drugs['ddd'] != 'NA']
    logger.info(f"\n=== DDD 정보가 있는 의약품 ===")
    logger.info(f"DDD 정보 있는 의약품: {len(ddd_drugs)}개")
    logger.info(f"DDD 정보 없는 의약품: {len(actual_drugs) - len(ddd_drugs)}개")

    # 샘플 데이터 확인
    logger.info(f"\n=== 샘플 의약품 (처음 10개) ===")
    sample_drugs = actual_drugs.head(10)
    for _, row in sample_drugs.iterrows():
        logger.info(f"{row['atc_code']}: {row['atc_name']} (DDD: {row['ddd']} {row['uom']})")

    # 요약 통계
    logger.info(f"\n=== 요약 통계 ===")
    logger.info(f"전체 행 수: {len(df)}")
    logger.info(f"실제 의약품 수 (Level 5): {len(actual_drugs)}")
    logger.info(f"DDD 정보 있는 의약품 수: {len(ddd_drugs)}")
    logger.info(f"ATC 1단계별 의약품 수: {len(first_level_stats)}")

    return {
        'total_rows': len(df),
        'actual_drugs': len(actual_drugs),
        'ddd_drugs': len(ddd_drugs),
        'first_level_distribution': first_level_stats.to_dict(),
        'level_distribution': level_stats.to_dict()
    }

if __name__ == "__main__":
    file_path = "atcd/output/WHO ATC-DDD 2025-06-26.csv"

    try:
        results = analyze_who_atc_data(file_path)
        logger.info("분석이 완료되었습니다!")
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
