import xml.etree.ElementTree as ET
import json
import os

def strip_ns(tag):
    # 네임스페이스 제거
    return tag.split('}')[-1] if '}' in tag else tag

def parse_single_drug(xml_file_path, output_file_path):
    print(f"XML 파일을 파싱 중: {xml_file_path}")

    context = ET.iterparse(xml_file_path, events=('start', 'end'))
    for event, elem in context:
        if event == 'end' and strip_ns(elem.tag) == 'drug':
            drug_data = {}
            for child in elem:
                tag = strip_ns(child.tag)
                if tag == 'drugbank-id':
                    drug_data.setdefault('drugbank_id', []).append(child.text)
                elif tag in ['name', 'description', 'cas-number', 'unii', 'state']:
                    drug_data[tag] = child.text
                elif tag == 'groups':
                    drug_data['groups'] = [g.text for g in child if strip_ns(g.tag) == 'group']
                elif tag == 'synonyms':
                    drug_data['synonyms'] = [s.text for s in child if strip_ns(s.tag) == 'synonym']
                # 필요한 필드 추가로 추출 가능

            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(drug_data, f, ensure_ascii=False, indent=2)
            print(f"저장 완료: {output_file_path}")
            break

if __name__ == "__main__":
    parse_single_drug("의약품데이터/drugbank_data/atc_split/atc_N.xml", "single_drug_data_final.json")
