#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DrugBank XML 데이터의 각 필드별 결측값 비율 분석 (간단한 버전)
"""

import re
import pandas as pd
from collections import defaultdict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_missing_values_simple(xml_file_path, sample_size=500):
    """
    정규표현식을 사용하여 DrugBank XML 파일의 각 필드별 결측값 비율을 분석

    Args:
        xml_file_path (str): XML 파일 경로
        sample_size (int): 분석할 샘플 크기
    """
    logger.info(f"결측값 분석 시작: {xml_file_path}")

    # 필드별 통계를 저장할 딕셔너리
    field_stats = defaultdict(lambda: {'present': 0, 'missing': 0, 'empty': 0})

    # 스키마에서 정의된 주요 필드들
    main_fields = [
        'drugbank-id', 'name', 'description', 'cas-number', 'unii',
        'average-mass', 'monoisotopic-mass', 'state', 'groups',
        'synthesis-reference', 'indication', 'pharmacodynamics',
        'mechanism-of-action', 'toxicity', 'metabolism', 'absorption',
        'half-life', 'protein-binding', 'route-of-elimination',
        'volume-of-distribution', 'clearance', 'classification',
        'salts', 'synonyms', 'products', 'international-brands',
        'mixtures', 'packagers', 'manufacturers', 'prices',
        'categories', 'affected-organisms', 'dosages', 'atc-codes',
        'ahfs-codes', 'pdb-entries', 'fda-label', 'msds', 'patents',
        'food-interactions', 'drug-interactions', 'sequences',
        'calculated-properties', 'experimental-properties',
        'external-identifiers', 'external-links', 'pathways',
        'reactions', 'snp-effects', 'snp-adverse-drug-reactions',
        'targets', 'enzymes', 'carriers', 'transporters'
    ]

    drug_count = 0

    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # drug 태그들을 찾기
        drug_pattern = r'(<drug[^>]*>.*?</drug>)'
        drug_matches = re.findall(drug_pattern, content, re.DOTALL)

        logger.info(f"총 {len(drug_matches)}개의 drug 요소 발견")

        for i, drug_text in enumerate(drug_matches):
            drug_count += 1

            # 각 필드별 존재 여부 확인
            for field in main_fields:
                # 필드 태그가 존재하는지 확인
                field_pattern = f'<{field}[^>]*>(.*?)</{field}>'
                field_match = re.search(field_pattern, drug_text, re.DOTALL)

                if field_match:
                    # 필드가 존재하는 경우, 내용이 있는지 확인
                    field_content = field_match.group(1).strip()
                    if field_content:
                        field_stats[field]['present'] += 1
                    else:
                        field_stats[field]['empty'] += 1
                else:
                    # 필드가 존재하지 않는 경우
                    field_stats[field]['missing'] += 1

            # 진행상황 출력
            if drug_count % 100 == 0:
                logger.info(f"처리된 의약품 수: {drug_count}")

            # 샘플 크기에 도달하면 중단
            if sample_size and drug_count >= sample_size:
                logger.info(f"샘플 크기 {sample_size}에 도달하여 분석을 중단합니다.")
                break

    except Exception as e:
        logger.error(f"파일 처리 중 오류 발생: {e}")
        return None

    logger.info(f"총 분석된 의약품 수: {drug_count}")

    # 결과를 DataFrame으로 변환
    results = []
    for field, stats in field_stats.items():
        total = stats['present'] + stats['missing'] + stats['empty']
        if total > 0:
            present_rate = (stats['present'] / total) * 100
            missing_rate = (stats['missing'] / total) * 100
            empty_rate = (stats['empty'] / total) * 100

            results.append({
                'field': field,
                'total_drugs': total,
                'present_count': stats['present'],
                'missing_count': stats['missing'],
                'empty_count': stats['empty'],
                'present_rate': round(present_rate, 2),
                'missing_rate': round(missing_rate, 2),
                'empty_rate': round(empty_rate, 2)
            })

    df = pd.DataFrame(results)

    # 결측률 순으로 정렬
    df = df.sort_values('missing_rate', ascending=False)

    return df

def print_missing_analysis(df):
    """결측값 분석 결과를 출력"""
    print("\n" + "="*80)
    print("DrugBank XML 데이터 필드별 결측값 분석 결과")
    print("="*80)

    print(f"\n총 분석된 의약품 수: {df['total_drugs'].iloc[0] if len(df) > 0 else 0}")

    print("\n" + "-"*80)
    print("결측률이 높은 필드 (상위 20개)")
    print("-"*80)
    print(f"{'필드명':<30} {'총 개수':<8} {'존재':<8} {'결측':<8} {'빈값':<8} {'결측률(%)':<10}")
    print("-"*80)

    for _, row in df.head(20).iterrows():
        print(f"{row['field']:<30} {row['total_drugs']:<8} {row['present_count']:<8} "
              f"{row['missing_count']:<8} {row['empty_count']:<8} {row['missing_rate']:<10.2f}")

    print("\n" + "-"*80)
    print("결측률이 낮은 필드 (하위 20개)")
    print("-"*80)
    print(f"{'필드명':<30} {'총 개수':<8} {'존재':<8} {'결측':<8} {'빈값':<8} {'결측률(%)':<10}")
    print("-"*80)

    for _, row in df.tail(20).iterrows():
        print(f"{row['field']:<30} {row['total_drugs']:<8} {row['present_count']:<8} "
              f"{row['missing_count']:<8} {row['empty_count']:<8} {row['missing_rate']:<10.2f}")

    # 요약 통계
    print("\n" + "="*80)
    print("요약 통계")
    print("="*80)

    high_missing = df[df['missing_rate'] > 50]
    medium_missing = df[(df['missing_rate'] > 20) & (df['missing_rate'] <= 50)]
    low_missing = df[df['missing_rate'] <= 20]

    print(f"결측률 > 50%: {len(high_missing)}개 필드")
    print(f"결측률 20-50%: {len(medium_missing)}개 필드")
    print(f"결측률 ≤ 20%: {len(low_missing)}개 필드")

    # 필수 필드 확인 (스키마에서 minOccurs="1"인 필드들)
    essential_fields = ['drugbank-id', 'name', 'description', 'cas-number', 'unii', 'groups',
                       'general-references', 'synthesis-reference', 'indication', 'pharmacodynamics',
                       'mechanism-of-action', 'toxicity', 'metabolism', 'absorption', 'half-life',
                       'protein-binding', 'route-of-elimination', 'volume-of-distribution', 'clearance',
                       'salts', 'synonyms', 'products', 'international-brands', 'mixtures', 'packagers',
                       'manufacturers', 'prices', 'categories', 'affected-organisms', 'dosages',
                       'atc-codes', 'ahfs-codes', 'pdb-entries', 'patents', 'food-interactions',
                       'drug-interactions', 'experimental-properties', 'external-identifiers',
                       'external-links', 'pathways', 'reactions', 'snp-effects', 'snp-adverse-drug-reactions',
                       'targets', 'enzymes', 'carriers', 'transporters']

    print(f"\n필수 필드 (스키마상 minOccurs='1') 결측률:")
    for field in essential_fields:
        if field in df['field'].values:
            row = df[df['field'] == field].iloc[0]
            print(f"  {field}: {row['missing_rate']:.2f}%")

def main():
    """메인 함수"""
    xml_file = "의약품데이터/drugbank_data/full database.xml"

    # 샘플 크기 설정
    sample_size = 500  # 500개 샘플로 분석

    # 결측값 분석 실행
    df = analyze_missing_values_simple(xml_file, sample_size)

    if df is not None:
        # 결과 출력
        print_missing_analysis(df)

        # CSV 파일로 저장
        output_file = "의약품데이터/missing_values_analysis.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n분석 결과가 저장되었습니다: {output_file}")

        # 상세 결과를 텍스트 파일로도 저장
        with open("의약품데이터/missing_values_analysis.txt", 'w', encoding='utf-8') as f:
            f.write("DrugBank XML 데이터 필드별 결측값 분석 결과\n")
            f.write("="*50 + "\n\n")
            f.write(f"총 분석된 의약품 수: {df['total_drugs'].iloc[0] if len(df) > 0 else 0}\n\n")

            f.write("전체 필드별 결측값 현황:\n")
            f.write("-"*50 + "\n")
            for _, row in df.iterrows():
                f.write(f"{row['field']}: {row['missing_rate']:.2f}% 결측\n")

        print(f"상세 결과가 저장되었습니다: 의약품데이터/missing_values_analysis.txt")
    else:
        print("분석 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()
