import os
import glob
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm

# ==========================================
# 설정 (Configuration)
# ==========================================
API_KEY = os.environ["OPENAI_API_KEY"]  # 여기에 API 키를 입력하거나 환경변수로 설정하세요.
SOURCE_FOLDER = "data/top_50_drugs"
MODEL_NAME = "gpt-4.1"  # 요청하신 모델명 (존재하지 않는 경우 gpt-4o 등으로 변경 필요)
FILE_LIMIT = 25
OUTPUT_XLSX = "output/imsang_questions_100.xlsx"
OUTPUT_CSV = "output/imsang_questions_100.csv"
TEMP_SAVE_INTERVAL = 5  # 5개 약물마다 임시 저장
TEMP_XLSX = "output/temp_imsang_questions.xlsx"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", API_KEY))

# ==========================================
# 프롬프트 설계 (System & One-Shot)
# ==========================================

SYSTEM_PROMPT = """
You are an expert medical education specialist and question generator.
Your task is to generate high-quality 'Clinical Reasoning True/False Questions' based on the provided drug information.
Focus on clinical vignettes, drug interactions, mechanisms of action, and toxicity.
"""

# One-Shot 예제 (트립토판 예시 활용)
ONE_SHOT_EXAMPLE = """
*** Example Input (Drug: Tryptophan) ***
[Information about Tryptophan including pharmacodynamics, interactions with Fluoxetine, toxicity signs like agitation and sweating...]

*** Example Output JSON ***
{
  "questions": [
    {
      "case_scenario": "A 45-year-old female with Major Depressive Disorder taking Fluoxetine presents with tremor, sweating, and agitation after starting a high-dose Tryptophan supplement.",
      "question": "The patient's presentation is likely due to a pharmacodynamic interaction increasing the risk of serotonin syndrome.",
      "label": "T"
    },
    {
      "case_scenario": "A 60-year-old male asks his physician how Tryptophan helps with sleep.",
      "question": "The efficacy of Tryptophan in sleep is mediated by its role as a precursor for melatonin synthesis.",
      "label": "T"
    },
    {
      "case_scenario": "A 30-year-old male on Lorazepam for anxiety asks if he can take Tryptophan.",
      "question": "Combining Tryptophan with Lorazepam decreases the risk of CNS depression.",
      "label": "F"
    },
    {
      "case_scenario": "A toddler ingested Tryptophan tablets and presents with diarrhea and hyperactive reflexes.",
      "question": "These symptoms are inconsistent with Tryptophan overdose.",
      "label": "F"
    }
  ]
}
"""

def create_user_prompt(drug_name, drug_content):
    return f"""
Here is the detailed information for the drug: "{drug_name}".
Based on this data, generate exactly 4 clinical reasoning True/False questions.

Requirements:
1. **Balance**: Generate exactly 2 True (T) and 2 False (F) questions.
2. **Context**: Each question must have a 'case_scenario' (clinical vignette) and a specific 'question' statement.
3. **Label**: Use 'T' for True and 'F' for False.
4. **Format**: Return ONLY a valid JSON object with the key "questions". Do not include markdown formatting.

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
        tqdm.write(f"Error reading file {file_path}: {e}")
        return []

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": create_user_prompt(drug_name, content)}
            ],
            temperature=0.7,
            response_format={"type": "json_object"} # JSON 강제 출력 (모델 지원 시)
        )

        response_content = response.choices[0].message.content
        data = json.loads(response_content)

        questions_data = []
        for item in data.get('questions', []):
            questions_data.append({
                "drug_name": drug_name,
                "case_scenario": item['case_scenario'],
                "question": item['question'],
                "label": item['label']
            })

        return questions_data

    except Exception as e:
        tqdm.write(f"Failed to generate for {drug_name}: {e}")
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
            df_temp = df_temp[['drug_name', 'case_scenario', 'question', 'label']]
            df_temp.to_excel(TEMP_XLSX, index=False)
            tqdm.write(f"✓ 임시 저장 완료: {idx}개 약물 처리 ({len(all_results)}개 질문) → {TEMP_XLSX}")

    # 3. 최종 결과 저장
    if all_results:
        df = pd.DataFrame(all_results)

        # 컬럼 순서 강제 지정
        df = df[['drug_name', 'case_scenario', 'question', 'label']]

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
