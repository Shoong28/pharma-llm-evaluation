#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DrugBank XML 데이터를 ATC 코드 1단계별로 분할하는 안전한 스크립트
"""

import xml.etree.ElementTree as ET
import os
import sys
from collections import defaultdict
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_atc_codes_from_text(text):
    """
    텍스트에서 ATC 코드를 추출하는 함수
    """
    atc_codes = []

    # ATC 코드 패턴 찾기 (예: <atc-code code="A10BA02">)
    atc_pattern = r'<atc-code\s+code="([^"]+)">'
    atc_matches = re.findall(atc_pattern, text)

    for atc_code in atc_matches:
        if len(atc_code) >= 1:
            # 첫 번째 문자가 ATC 1단계 코드
            first_level = atc_code[0]
            atc_codes.append(first_level)

    return list(set(atc_codes))  # 중복 제거

def split_drugbank_by_atc_safe(input_file, output_dir):
    """
    안전한 방법으로 DrugBank XML 파일을 ATC 코드 1단계별로 분할
    """
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # ATC 코드별로 drug 블록들을 그룹화
    atc_groups = defaultdict(list)
    total_drugs = 0
    drugs_with_atc = 0

    logger.info(f"XML 파일 처리 시작: {input_file}")

    # 파일을 텍스트로 읽어서 처리
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # drug 태그들을 찾기
    drug_pattern = r'(<drug[^>]*>.*?</drug>)'
    drug_matches = re.findall(drug_pattern, content, re.DOTALL)

    logger.info(f"총 {len(drug_matches)}개의 drug 요소 발견")

    for i, drug_text in enumerate(drug_matches):
        total_drugs += 1

        # ATC 코드 추출
        atc_codes = extract_atc_codes_from_text(drug_text)

        if atc_codes:
            drugs_with_atc += 1
            # 각 ATC 1단계 코드별로 drug를 그룹화
            for atc_code in atc_codes:
                atc_groups[atc_code].append(drug_text)
        else:
            # ATC 코드가 없는 경우 'NO_ATC' 그룹에 추가
            atc_groups['NO_ATC'].append(drug_text)

        # 진행상황 출력
        if total_drugs % 1000 == 0:
            logger.info(f"처리된 의약품 수: {total_drugs}")

    logger.info(f"총 의약품 수: {total_drugs}")
    logger.info(f"ATC 코드가 있는 의약품 수: {drugs_with_atc}")

    # 원본 파일의 헤더 정보 추출
    header_match = re.search(r'(<drugbank[^>]*>)', content)
    header = header_match.group(1) if header_match else '<drugbank version="5.1.11" exported-on="2024-01-01">'

    # ATC 코드별로 XML 파일 생성
    for atc_code, drugs in atc_groups.items():
        if not drugs:
            continue

        logger.info(f"ATC 코드 {atc_code} 처리 중... ({len(drugs)}개 의약품)")

        # XML 파일 생성
        output_file = os.path.join(output_dir, f'atc_{atc_code}.xml')

        with open(output_file, 'w', encoding='utf-8') as f:
            # XML 선언
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')

            # 헤더
            f.write(header + '\n')

            # drug 요소들
            for drug_text in drugs:
                f.write(drug_text + '\n')

            # 닫는 태그
            f.write('</drugbank>\n')

        logger.info(f"저장 완료: {output_file}")

    # 요약 정보 출력
    logger.info("\n=== ATC 코드별 분할 결과 ===")
    for atc_code, drugs in sorted(atc_groups.items()):
        if drugs:
            logger.info(f"ATC {atc_code}: {len(drugs)}개 의약품")

def get_atc_code_names():
    """
    ATC 코드 1단계별 이름 반환
    """
    return {
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
        'V': '기타 (Various)',
        'NO_ATC': 'ATC 코드 없음'
    }

if __name__ == "__main__":
    input_file = "drugbank_data/full database.xml"
    output_dir = "drugbank_data/atc_split"

    if not os.path.exists(input_file):
        logger.error(f"입력 파일을 찾을 수 없습니다: {input_file}")
        sys.exit(1)

    try:
        split_drugbank_by_atc_safe(input_file, output_dir)
        logger.info("ATC 코드별 분할이 완료되었습니다!")

        # ATC 코드별 이름 정보 출력
        atc_names = get_atc_code_names()
        logger.info("\n=== ATC 코드별 의미 ===")
        for code, name in atc_names.items():
            logger.info(f"{code}: {name}")

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
