#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATC N 파일의 필드별 결측값 비율 분석
"""

import re
import pandas as pd
from collections import defaultdict
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_atc_n_missing_values(xml_file_path):
    """
    ATC N XML 파일의 각 필드별 결측값 비율을 분석

    Args:
        xml_file_path (str): XML 파일 경로
    """
    logger.info(f"ATC N 파일 결측값 분석 시작: {xml_file_path}")
    start_time = time.time()

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
        logger.info("XML 파일을 읽는 중...")
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info("drug 태그들을 찾는 중...")
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

            # 진행상황 출력 (1000개마다)
            if drug_count % 1000 == 0:
                elapsed_time = time.time() - start_time
                rate = drug_count / elapsed_time
                remaining = (len(drug_matches) - drug_count) / rate if rate > 0 else 0
                logger.info(f"처리된 의약품 수: {drug_count}/{len(drug_matches)} "
                          f"({drug_count/len(drug_matches)*100:.1f}%) "
                          f"예상 남은 시간: {remaining/60:.1f}분")

        elapsed_time = time.time() - start_time
        logger.info(f"분석 완료! 총 소요 시간: {elapsed_time/60:.1f}분")
        logger.info(f"총 분석된 의약품 수: {drug_count}")

    except Exception as e:
        logger.error(f"파일 처리 중 오류 발생: {e}")
        return None

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

def print_atc_n_missing_analysis(df):
    """ATC N 결측값 분석 결과를 출력"""
    print("\n" + "="*100)
    print("ATC N 파일 필드별 결측값 분석 결과")
    print("="*100)

    print(f"\n총 분석된 의약품 수: {df['total_drugs'].iloc[0] if len(df) > 0 else 0}")

    print("\n" + "-"*100)
    print("결측률이 높은 필드 (상위 25개)")
    print("-"*100)
    print(f"{'필드명':<35} {'총 개수':<10} {'존재':<10} {'결측':<10} {'빈값':<10} {'결측률(%)':<12}")
    print("-"*100)

    for _, row in df.head(25).iterrows():
        print(f"{row['field']:<35} {row['total_drugs']:<10} {row['present_count']:<10} "
              f"{row['missing_count']:<10} {row['empty_count']:<10} {row['missing_rate']:<12.2f}")

    print("\n" + "-"*100)
    print("결측률이 낮은 필드 (하위 25개)")
    print("-"*100)
    print(f"{'필드명':<35} {'총 개수':<10} {'존재':<10} {'결측':<10} {'빈값':<10} {'결측률(%)':<12}")
    print("-"*100)

    for _, row in df.tail(25).iterrows():
        print(f"{row['field']:<35} {row['total_drugs']:<10} {row['present_count']:<10} "
              f"{row['missing_count']:<10} {row['empty_count']:<10} {row['missing_rate']:<12.2f}")

    # 요약 통계
    print("\n" + "="*100)
    print("요약 통계")
    print("="*100)

    high_missing = df[df['missing_rate'] > 50]
    medium_missing = df[(df['missing_rate'] > 20) & (df['missing_rate'] <= 50)]
    low_missing = df[df['missing_rate'] <= 20]

    print(f"결측률 > 50%: {len(high_missing)}개 필드")
    print(f"결측률 20-50%: {len(medium_missing)}개 필드")
    print(f"결측률 ≤ 20%: {len(low_missing)}개 필드")

    # ATC N 관련 특별 분석
    print(f"\n" + "="*100)
    print("ATC N 관련 특별 분석")
    print("="*100)

    # ATC 코드 분석
    atc_row = df[df['field'] == 'atc-codes']
    if not atc_row.empty:
        atc_present = atc_row['present_count'].iloc[0]
        atc_total = atc_row['total_drugs'].iloc[0]
        print(f"ATC 코드가 있는 약물: {atc_present}/{atc_total} ({atc_present/atc_total*100:.2f}%)")

    # 주요 신경계 관련 필드 분석
    neuro_fields = ['indication', 'pharmacodynamics', 'mechanism-of-action', 'toxicity', 'metabolism']
    print(f"\n신경계 약물 관련 주요 필드 결측률:")
    for field in neuro_fields:
        if field in df['field'].values:
            row = df[df['field'] == field].iloc[0]
            print(f"  {field}: {row['missing_rate']:.2f}% (존재: {row['present_count']})")

def main():
    """메인 함수"""
    xml_file = "의약품데이터/drugbank_data/atc_split/atc_N.xml"

    # ATC N 파일 결측값 분석 실행
    df = analyze_atc_n_missing_values(xml_file)

    if df is not None:
        # 결과 출력
        print_atc_n_missing_analysis(df)

        # CSV 파일로 저장
        output_file = "의약품데이터/atc_n_missing_values_analysis.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nATC N 분석 결과가 저장되었습니다: {output_file}")

        # 상세 결과를 텍스트 파일로도 저장
        with open("의약품데이터/atc_n_missing_values_analysis.txt", 'w', encoding='utf-8') as f:
            f.write("ATC N 파일 필드별 결측값 분석 결과\n")
            f.write("="*60 + "\n\n")
            f.write(f"총 분석된 의약품 수: {df['total_drugs'].iloc[0] if len(df) > 0 else 0}\n\n")

            f.write("전체 필드별 결측값 현황:\n")
            f.write("-"*60 + "\n")
            for _, row in df.iterrows():
                f.write(f"{row['field']}: {row['missing_rate']:.2f}% 결측 "
                       f"(존재: {row['present_count']}, 결측: {row['missing_count']}, 빈값: {row['empty_count']})\n")

        print(f"상세 결과가 저장되었습니다: 의약품데이터/atc_n_missing_values_analysis.txt")

        # 전체 데이터와 비교
        print(f"\n" + "="*100)
        print("전체 DrugBank vs ATC N 비교")
        print("="*100)

        # 전체 분석 결과 읽기
        try:
            full_df = pd.read_csv("의약품데이터/full_missing_values_analysis.csv")
            print(f"전체 DrugBank: {full_df['total_drugs'].iloc[0]}개 약물")
            print(f"ATC N: {df['total_drugs'].iloc[0]}개 약물")

            # 주요 필드 비교
            key_fields = ['name', 'drugbank-id', 'description', 'cas-number', 'atc-codes', 'products', 'indication']
            print(f"\n주요 필드 결측률 비교:")
            print(f"{'필드명':<20} {'전체(%)':<10} {'ATC N(%)':<10} {'차이(%)':<10}")
            print("-"*50)

            for field in key_fields:
                if field in full_df['field'].values and field in df['field'].values:
                    full_rate = full_df[full_df['field'] == field]['missing_rate'].iloc[0]
                    atc_n_rate = df[df['field'] == field]['missing_rate'].iloc[0]
                    diff = atc_n_rate - full_rate
                    print(f"{field:<20} {full_rate:<10.2f} {atc_n_rate:<10.2f} {diff:<10.2f}")

        except FileNotFoundError:
            print("전체 분석 결과 파일을 찾을 수 없습니다.")

    else:
        print("ATC N 분석 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()
