#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATC 코드가 없는 의약품들의 그룹을 확인하는 스크립트
"""

import re
import logging
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_drug_groups(input_file, sample_size=50):
    """
    ATC 코드가 없는 의약품들의 그룹을 확인
    """
    logger.info(f"의약품 그룹 확인 시작: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # drug 태그들을 찾기
    drug_pattern = r'(<drug[^>]*>.*?</drug>)'
    drug_matches = re.findall(drug_pattern, content, re.DOTALL)

    logger.info(f"총 {len(drug_matches)}개의 drug 요소 발견")

    # ATC 코드가 없는 의약품들만 필터링
    drugs_without_atc = []
    drugs_with_atc = []

    for drug_text in drug_matches:
        atc_pattern = r'<atc-codes>'
        if re.search(atc_pattern, drug_text):
            drugs_with_atc.append(drug_text)
        else:
            drugs_without_atc.append(drug_text)

    logger.info(f"ATC 코드 있는 의약품: {len(drugs_with_atc)}개")
    logger.info(f"ATC 코드 없는 의약품: {len(drugs_without_atc)}개")

    # ATC 코드가 없는 의약품들의 그룹 분석
    group_stats = defaultdict(int)
    approved_without_atc = 0
    experimental_without_atc = 0

    logger.info(f"\n=== ATC 코드가 없는 의약품 그룹 분석 (샘플 {sample_size}개) ===")

    for i, drug_text in enumerate(drugs_without_atc[:sample_size]):
        # drug의 type 속성 확인
        type_match = re.search(r'<drug[^>]*type="([^"]*)"', drug_text)
        drug_type = type_match.group(1) if type_match else "unknown"

        # groups 정보 추출
        groups_pattern = r'<groups>.*?</groups>'
        groups_match = re.search(groups_pattern, drug_text, re.DOTALL)

        if groups_match:
            groups_text = groups_match.group(0)
            # 각 group 확인
            group_matches = re.findall(r'<group>([^<]+)</group>', groups_text)

            for group in group_matches:
                group_stats[group] += 1

                if group == 'approved':
                    approved_without_atc += 1
                elif group == 'experimental':
                    experimental_without_atc += 1

        # 의약품명 추출
        name_pattern = r'<name>([^<]+)</name>'
        name_match = re.search(name_pattern, drug_text)
        drug_name = name_match.group(1) if name_match else "Unknown"

        logger.info(f"{i+1}. {drug_name} (type: {drug_type}, groups: {group_matches if groups_match else 'N/A'})")

    logger.info(f"\n=== 전체 ATC 코드 없는 의약품 그룹 통계 ===")

    # 전체 통계
    total_group_stats = defaultdict(int)
    total_approved_without_atc = 0
    total_experimental_without_atc = 0

    for drug_text in drugs_without_atc:
        groups_pattern = r'<groups>.*?</groups>'
        groups_match = re.search(groups_pattern, drug_text, re.DOTALL)

        if groups_match:
            groups_text = groups_match.group(0)
            group_matches = re.findall(r'<group>([^<]+)</group>', groups_text)

            for group in group_matches:
                total_group_stats[group] += 1

                if group == 'approved':
                    total_approved_without_atc += 1
                elif group == 'experimental':
                    total_experimental_without_atc += 1

    logger.info(f"승인된 의약품이지만 ATC 코드 없음: {total_approved_without_atc}개")
    logger.info(f"실험적 의약품이면서 ATC 코드 없음: {total_experimental_without_atc}개")

    logger.info(f"\n=== 전체 그룹별 통계 ===")
    for group, count in sorted(total_group_stats.items()):
        logger.info(f"{group}: {count}개")

    # ATC 코드가 있는 의약품들의 그룹도 확인
    logger.info(f"\n=== ATC 코드가 있는 의약품 그룹 통계 ===")
    atc_group_stats = defaultdict(int)

    for drug_text in drugs_with_atc:
        groups_pattern = r'<groups>.*?</groups>'
        groups_match = re.search(groups_pattern, drug_text, re.DOTALL)

        if groups_match:
            groups_text = groups_match.group(0)
            group_matches = re.findall(r'<group>([^<]+)</group>', groups_text)

            for group in group_matches:
                atc_group_stats[group] += 1

    for group, count in sorted(atc_group_stats.items()):
        logger.info(f"{group}: {count}개")

if __name__ == "__main__":
    input_file = "drugbank_data/full database.xml"

    try:
        check_drug_groups(input_file, sample_size=30)
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
