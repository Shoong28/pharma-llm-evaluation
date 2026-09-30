import re
import json

def extract_drug_block(xml_path, drug_index=1):
    """
    XML 파일에서 지정된 번째의 drug 블록을 추출

    Args:
        xml_path (str): 원본 XML 파일 경로
        drug_index (int): 추출할 drug의 번째 (1부터 시작)
    """
    print(f"XML 파일에서 {drug_index}번째 drug 블록을 추출 중...")

    drug_count = 0
    inside = False
    drug_content = ""
    depth = 0

    with open(xml_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not inside and '<drug ' in line:
                drug_count += 1
                if drug_count == drug_index:
                    inside = True
                    print(f"{drug_index}번째 drug 블록을 찾았습니다.")

            if inside:
                drug_content += line
                # depth 계산
                depth += line.count('<drug') - line.count('</drug')
                if depth == 0 and '</drug>' in line:
                    break

    if not drug_content:
        print(f"{drug_index}번째 drug 블록을 찾을 수 없습니다.")
        return None

    return drug_content

def parse_drug_content(drug_content):
    """
    Drug 블록 내용을 파싱하여 딕셔너리로 변환
    """
    print("약물 정보를 파싱 중...")

    drug_dict = {}

    # 기본 정보들 추출
    basic_fields = [
        'name', 'description', 'cas-number', 'unii', 'average-mass',
        'monoisotopic-mass', 'state', 'indication', 'pharmacodynamics',
        'mechanism-of-action', 'toxicity', 'metabolism', 'absorption',
        'half-life', 'protein-binding', 'route-of-elimination',
        'volume-of-distribution', 'clearance'
    ]

    for field in basic_fields:
        pattern = f'<{field}>(.*?)</{field}>'
        match = re.search(pattern, drug_content, re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value:  # 빈 값이 아닌 경우만 저장
                drug_dict[field.replace('-', '_')] = value

    # DrugBank ID들 추출
    drugbank_ids = re.findall(r'<drugbank-id[^>]*>(.*?)</drugbank-id>', drug_content)
    if drugbank_ids:
        drug_dict['drugbank_id'] = drugbank_ids

    # Groups 추출
    groups_match = re.search(r'<groups>(.*?)</groups>', drug_content, re.DOTALL)
    if groups_match:
        groups_content = groups_match.group(1)
        groups = re.findall(r'<group>(.*?)</group>', groups_content)
        if groups:
            drug_dict['groups'] = groups

    # Synonyms 추출
    synonyms_match = re.search(r'<synonyms>(.*?)</synonyms>', drug_content, re.DOTALL)
    if synonyms_match:
        synonyms_content = synonyms_match.group(1)
        synonyms = re.findall(r'<synonym[^>]*>(.*?)</synonym>', synonyms_content)
        if synonyms:
            drug_dict['synonyms'] = synonyms

    # ATC Codes 추출
    atc_codes_match = re.search(r'<atc-codes>(.*?)</atc-codes>', drug_content, re.DOTALL)
    if atc_codes_match:
        atc_content = atc_codes_match.group(1)
        atc_codes = re.findall(r'<atc-code[^>]*>(.*?)</atc-code>', atc_content, re.DOTALL)
        if atc_codes:
            drug_dict['atc_codes'] = atc_codes

    # Drug Interactions 추출
    interactions_match = re.search(r'<drug-interactions>(.*?)</drug-interactions>', drug_content, re.DOTALL)
    if interactions_match:
        interactions_content = interactions_match.group(1)
        interactions = re.findall(r'<drug-interaction>(.*?)</drug-interaction>', interactions_content, re.DOTALL)
        if interactions:
            drug_dict['drug_interactions'] = interactions

    # Products 추출
    products_match = re.search(r'<products>(.*?)</products>', drug_content, re.DOTALL)
    if products_match:
        products_content = products_match.group(1)
        products = re.findall(r'<product>(.*?)</product>', products_content, re.DOTALL)
        if products:
            drug_dict['products'] = products

    # External Identifiers 추출
    ext_ids_match = re.search(r'<external-identifiers>(.*?)</external-identifiers>', drug_content, re.DOTALL)
    if ext_ids_match:
        ext_ids_content = ext_ids_match.group(1)
        ext_ids = re.findall(r'<external-identifier>(.*?)</external-identifier>', ext_ids_content, re.DOTALL)
        if ext_ids:
            drug_dict['external_identifiers'] = ext_ids

    return drug_dict

def parse_drug_by_index(xml_file_path, drug_index, output_file_path):
    """
    XML 파일에서 지정된 번째의 drug를 파싱하여 JSON으로 저장

    Args:
        xml_file_path (str): 원본 XML 파일 경로
        drug_index (int): 파싱할 drug의 번째 (1부터 시작)
        output_file_path (str): 출력 JSON 파일 경로
    """
    # 1단계: drug 블록 추출
    drug_content = extract_drug_block(xml_file_path, drug_index)

    if drug_content is None:
        return None

    # 2단계: 추출된 블록 파싱
    drug_dict = parse_drug_content(drug_content)

    # JSON 파일로 저장
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(drug_dict, f, ensure_ascii=False, indent=2)

    print(f"약물 정보가 성공적으로 저장되었습니다: {output_file_path}")

    # 기본 정보 출력
    print(f"\n=== 파싱된 약물 정보 요약 ===")
    print(f"약물명: {drug_dict.get('name', 'N/A')}")
    print(f"DrugBank ID: {drug_dict.get('drugbank_id', 'N/A')}")
    print(f"CAS 번호: {drug_dict.get('cas_number', 'N/A')}")
    print(f"UNII: {drug_dict.get('unii', 'N/A')}")
    print(f"상태: {drug_dict.get('state', 'N/A')}")

    # 그룹 정보
    if 'groups' in drug_dict:
        print(f"그룹: {', '.join(drug_dict['groups'])}")

    # 동의어 수
    if 'synonyms' in drug_dict:
        print(f"동의어 수: {len(drug_dict['synonyms'])}")

    # product 수
    if 'products' in drug_dict:
        print(f"product 수: {len(drug_dict['products'])}")

    return drug_dict

if __name__ == "__main__":
    xml_file = "drugbank_data/atc_split/atc_N.xml"

    # 사용자가 원하는 번째의 drug를 파싱
    drug_index = 1  # 1번째 drug (원하는 번호로 변경 가능)
    output_file = f"drug_{drug_index}_complete.json"

    drug_info = parse_drug_by_index(xml_file, drug_index, output_file)
