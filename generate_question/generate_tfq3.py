'''
TFQ3
처방 시나리오를 제공했을 때 해당 처방이 적절한지 부적절한지 판단하는 문항 생성
'''



import os
import glob
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm


# ==========================================
# 설정 (Configuration)
# ==========================================
QUESTION_TYPE = "tfq3"
SOURCE_FOLDER = "data/top_50_drugs"
MODEL_NAME = "gpt-4.1"  # 문항을 생성할 모델
FILE_LIMIT = 25 # 상위 25개만 선택
OUTPUT_XLSX = f"output/{QUESTION_TYPE}_100.xlsx"
OUTPUT_CSV = f"output/{QUESTION_TYPE}_100.csv"
TEMP_SAVE_INTERVAL = 5  # 5개 약물마다 임시 저장
TEMP_XLSX = f"output/temp_{QUESTION_TYPE}.xlsx"

API_KEY = os.environ["OPENAI_API_KEY"]  # 여기에 API 키를 입력하거나 환경변수로 설정하세요.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", API_KEY))

# ==========================================
# 프롬프트 설계 (System & One-Shot: 자연스러운 흐름)
# ==========================================

SYSTEM_PROMPT = """
You are an expert medical education specialist.
Your task is to generate high-quality, detailed 'Clinical Prescription Appropriateness Questions' (True/False) based on the provided drug information.

For each question, you must construct a rich clinical vignette:
1.  **Case Scenario**: A realistic and detailed clinical situation including patient demographics, history, and symptoms.
2.  **Prescription & Rationale**: A specific action taken by a physician AND the reason for it (e.g., "The physician prescribes X because...").
3.  **Question**: The question must always be: **"Is this prescription and the provided rationale clinically appropriate?"**

**Guidance for True/False Logic:**
* **True**: The prescription and rationale are fully supported by the text (correct indication, mechanism, and safety).
* **False**: The prescription is clinically inappropriate (e.g., contraindication, wrong indication, unsafe dosage) OR the rationale is clearly incorrect based on the text.
"""

# One-Shot 예제 (함정 없이 자연스러운 예시로 구성)
ONE_SHOT_EXAMPLE = """
*** Example Input (Drug: Tryptophan) ***
[Information about Tryptophan: contraindicated with MAOIs like Phenelzine; indicated for insomnia and SAD; overdose causes hyperreflexia...]

*** Example Output JSON ***
{
  "questions": [
    {
      "case_scenario": "A 35-year-old male with atypical depression has been managed on Phenelzine (an MAOI) for the past 6 months. He visits his psychiatrist reporting persistent low mood. The physician decides to prescribe L-Tryptophan 500 mg daily as an adjunct therapy to naturally boost serotonin levels.",
      "question": "Is this prescription and the provided rationale clinically appropriate?",
      "label": "F"
    },
    {
      "case_scenario": "A 28-year-old female presents with Seasonal Affective Disorder (SAD), describing symptoms that worsen every winter. She prefers nutritional precursors. Based on her diagnosis, the physician prescribes Tryptophan, explaining that it serves as a precursor for serotonin synthesis.",
      "question": "Is this prescription and the provided rationale clinically appropriate?",
      "label": "T"
    },
    {
      "case_scenario": "A 19-year-old male is brought to the ER with confusion, shivering, hyperreflexia, and profuse sweating after consuming a large amount of workout supplements containing amino acids. Suspecting anxiety, the attending physician administers an additional dose of Tryptophan to calm the patient.",
      "question": "Is this prescription and the provided rationale clinically appropriate?",
      "label": "F"
    },
    {
      "case_scenario": "A 55-year-old male complains of chronic insomnia and wants to avoid benzodiazepines. The doctor prescribes Tryptophan supplements, explaining that it promotes healthy sleep by acting as a precursor for melatonin.",
      "question": "Is this prescription and the provided rationale clinically appropriate?",
      "label": "T"
    }
  ]
}
"""

def create_user_prompt(drug_name, drug_content):
    return f"""
Here is the detailed information for the drug: "{drug_name}".
Based on this data, generate exactly 4 Clinical Prescription Appropriateness questions.

Requirements:
1.  **Detail**: The 'case_scenario' must be detailed and realistic.
2.  **Structure**: Use the 'Case Scenario' + 'Prescription & Rationale' format.
3.  **Question Text**: Use exactly: "Is this prescription and the provided rationale clinically appropriate?"
4.  **Balance**: Generate exactly 2 True (Appropriate) and 2 False (Inappropriate) questions.
5.  **Format**: Return ONLY a valid JSON object with the key "questions". Do not include markdown formatting.

{ONE_SHOT_EXAMPLE}

*** TARGET INPUT (Drug: {drug_name}) ***
{drug_content}

*** TARGET OUTPUT JSON ***
"""

# ==========================================
# 메인 로직 (Main Logic)
# ==========================================

def generate_questions_for_drug(file_path):
    drug_name = os.path.splitext(os.path.basename(file_path))[0]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    print(f"Generating questions for: {drug_name}...")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": create_user_prompt(drug_name, content)}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        response_content = response.choices[0].message.content
        data = json.loads(response_content)

        questions_data = []
        for item in data.get('questions', []):
            questions_data.append({
                "drug_name": drug_name,
                "case_scenario": item['case_scenario'],
                "question_text": item['question'],
                "ques": item['case_scenario'] + "\n" + item['question'],
                "label": item['label']
            })

        return questions_data

    except Exception as e:
        print(f"Failed to generate for {drug_name}: {e}")
        return []

def main():
    # 1. 파일 목록 가져오기 및 정렬
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Folder '{SOURCE_FOLDER}' not found.")
        return

    all_files = sorted(glob.glob(os.path.join(SOURCE_FOLDER, "*.txt")))
    target_files = all_files[:FILE_LIMIT] # 상위 25개만 선택

    if not target_files:
        print("No text files found.")
        return

    print(f"Found {len(all_files)} files. Processing first {len(target_files)} files.")

    # 2. 문제 생성 루프
    all_results = []

    # TQDM 진행바 추가
    for idx, file_path in enumerate(tqdm(target_files, desc="약물 처리 진행", unit="약물"), start=1):
        results = generate_questions_for_drug(file_path)
        all_results.extend(results)

        # 5개마다 임시 저장
        if idx % TEMP_SAVE_INTERVAL == 0:
            df_temp = pd.DataFrame(all_results)
            df_temp = df_temp[['drug_name', 'case_scenario', 'question_text', 'ques', 'label']]
            df_temp.to_excel(TEMP_XLSX, index=False)
            tqdm.write(f"✓ 임시 저장 완료: {idx}개 약물 처리 ({len(all_results)}개 질문) → {TEMP_XLSX}")

    # 3. 최종 결과 저장
    if all_results:
        df = pd.DataFrame(all_results)

        # 컬럼 순서 강제 지정
        df = df[['drug_name', 'case_scenario', 'question_text', 'ques', 'label']]

        # Excel 저장
        df.to_excel(OUTPUT_XLSX, index=False)
        tqdm.write(f"\n✓ 최종 Excel 저장: {OUTPUT_XLSX}")

        # CSV 저장
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        tqdm.write(f"✓ 최종 CSV 저장: {OUTPUT_CSV}")

        tqdm.write(f"✓ 총 생성된 질문 수: {len(df)}개")

        # 임시 파일 삭제
        if os.path.exists(TEMP_XLSX):
            os.remove(TEMP_XLSX)
            tqdm.write(f"✓ 임시 파일 삭제 완료: {TEMP_XLSX}")
    else:
        tqdm.write("No questions were generated.")

if __name__ == "__main__":
    main()
