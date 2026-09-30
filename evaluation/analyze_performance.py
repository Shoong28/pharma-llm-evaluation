import os
import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # GUI 없이 이미지 저장용 백엔드 설정
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
import re

# 한글 폰트 설정 제거 (시스템 호환성 문제 방지)
# plt.rcParams['font.family'] = 'AppleGothic'
# plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
DATA_DIR = os.environ.get('PHARMA_DATA_DIR', 'evaluation/data')
RESULT_DIR = os.environ.get('PHARMA_RESULT_DIR', 'evaluation/analysis_results')
EACH_PLOT_DIR = os.path.join(RESULT_DIR, 'each_plot')
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(EACH_PLOT_DIR, exist_ok=True)

# 프롬프트 전략 목록
PROMPTS = ['ao', 'cot', 'cove']

def clean_text(text):
    """텍스트 정제: 공백 제거 및 대문자 변환"""
    if pd.isna(text):
        return ""
    return str(text).strip().upper()

def parse_mcq(text):
    """MCQ 정답 추출 (A, B, C, D)"""
    text = clean_text(text)
    match = re.search(r'[ABCD]', text)
    return match.group(0) if match else "UNKNOWN"

def parse_tfq(text):
    """TFQ 정답 추출 (T, F)"""
    text = clean_text(text)
    if 'T' in text and 'F' not in text: return 'T'
    if 'F' in text and 'T' not in text: return 'F'
    if 'TRUE' in text: return 'T'
    if 'FALSE' in text: return 'F'
    # 간단한 파싱: T나 F로 시작하거나 포함되면 처리
    if text.startswith('T'): return 'T'
    if text.startswith('F'): return 'F'
    return "UNKNOWN"

def parse_maq(text):
    """MAQ 정답 추출 (Set of options)"""
    text = clean_text(text)
    # 콤마, 공백 등으로 분리 후 A,B,C,D만 추출
    found = set(re.findall(r'[ABCD]', text))
    return found

def parse_rq_full(text):
    """RQ 정답 추출 (Answer, Judgment) -> (A/B/C/D, T/F)"""
    text = clean_text(text)
    # 예상 포맷: "C,F" (정답 C, 판단 F) 또는 "C, T" 등
    # 순서가 [Answer], [Judgment] 인지 데이터 확인 필요.
    # 앞선 데이터 확인 결과: "C,F" -> Answer=C, Judgment=F

    answer = "UNKNOWN"
    judgment = "UNKNOWN"

    if ',' in text:
        parts = [p.strip() for p in text.split(',')]
        # 보통 알파벳(A-D)이 Answer, T/F가 Judgment
        for p in parts:
            if p in ['A', 'B', 'C', 'D']:
                answer = p
            elif p in ['T', 'F', 'TRUE', 'FALSE']:
                judgment = 'T' if 'T' in p else 'F'
    else:
        # 콤마가 없는 경우
        match_ans = re.search(r'[ABCD]', text)
        if match_ans: answer = match_ans.group(0)

        if 'T' in text and 'F' not in text: judgment = 'T'
        elif 'F' in text and 'T' not in text: judgment = 'F'

    return answer, judgment

def plot_confusion_matrix(y_true, y_pred, labels, title, filename):
    """Confusion Matrix 그리기 및 저장"""
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    # Predicted 축을 위쪽에 표시
    plt.gca().xaxis.set_label_position('top')
    plt.gca().xaxis.tick_top()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return cm

def analyze_file(filepath):
    filename = os.path.basename(filepath)
    print(f"Analyzing {filename}...")

    # 파일명에서 정보 추출 (예: gpt-4o_MCQ_merged.xlsx)
    parts = filename.replace('.xlsx', '').split('_')
    if len(parts) < 2:
        print(f"Skipping {filename}: unknown format")
        return []

    model_name = parts[0]
    q_type = parts[1] # MCQ, MAQ, RQ, TFQ...

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

    results = []

    # 문제 유형별 처리
    for prompt in PROMPTS:
        col_ans = f"{prompt}_ans"
        if col_ans not in df.columns:
            continue

        y_true = []
        y_pred = []
        labels = [] # Confusion Matrix용 레이블

        # 데이터 파싱 및 리스트 변환
        if q_type == 'MCQ':
            labels = ['A', 'B', 'C', 'D']
            for _, row in df.iterrows():
                y_true.append(parse_mcq(row['label']))
                y_pred.append(parse_mcq(row[col_ans]))

        elif q_type == 'MAQ':
            # MAQ는 각 선지(A,B,C,D)별로 바이너리(선택/미선택) 데이터로 변환하여 병합
            # Selected를 positive 위치(아래쪽)에 배치
            labels = ['Selected', 'Not Selected']
            temp_true = []
            temp_pred = []
            options = ['A', 'B', 'C', 'D']

            for _, row in df.iterrows():
                true_set = parse_maq(row['label'])
                pred_set = parse_maq(row[col_ans])

                for opt in options:
                    temp_true.append('Selected' if opt in true_set else 'Not Selected')
                    temp_pred.append('Selected' if opt in pred_set else 'Not Selected')

            y_true = temp_true
            y_pred = temp_pred

        elif q_type == 'RQ':
            # RQ는 두 가지 관점에서 분석: 1) Judgment(T/F), 2) Answer(A-D)

            # 1. Judgment Analysis
            labels_judg = ['T', 'F']
            y_true_judg = []
            y_pred_judg = []

            # 2. Answer Analysis
            labels_ans = ['A', 'B', 'C', 'D']
            y_true_ans = []
            y_pred_ans = []

            for _, row in df.iterrows():
                t_ans, t_judg = parse_rq_full(row['label'])
                p_ans, p_judg = parse_rq_full(row[col_ans])

                y_true_judg.append(t_judg)
                y_pred_judg.append(p_judg)

                y_true_ans.append(t_ans)
                y_pred_ans.append(p_ans)

            # --- Judgment CM ---
            total_judg = len(y_true_judg)
            valid_idx_judg = [i for i, (t, p) in enumerate(zip(y_true_judg, y_pred_judg)) if t in labels_judg and p in labels_judg]

            # 유효한 데이터만 추출
            yt_clean = [y_true_judg[i] for i in valid_idx_judg]
            yp_clean = [y_pred_judg[i] for i in valid_idx_judg]

            valid_count_judg = len(yt_clean)
            invalid_count_judg = total_judg - valid_count_judg

            # Overall Accuracy (형식 오류 포함)
            correct_judg = sum([1 for yt, yp in zip(yt_clean, yp_clean) if yt == yp])
            overall_acc_judg = correct_judg / total_judg if total_judg > 0 else 0

            if valid_idx_judg:
                plot_filename = os.path.join(EACH_PLOT_DIR, f"CM_{model_name}_{q_type}_Judgment_{prompt}.png")
                plot_confusion_matrix(yt_clean, yp_clean, labels_judg, f"{model_name} RQ Judgment ({prompt.upper()})", plot_filename)

                # Metrics for Judgment (Valid Only)
                p, r, f, _ = precision_recall_fscore_support(yt_clean, yp_clean, average='macro', zero_division=0)
                results.append({
                    'Model': model_name, 'Type': 'RQ_Judgment', 'Prompt': prompt,
                    'Overall_Accuracy': overall_acc_judg, # 전체 정확도
                    'Valid_Accuracy': accuracy_score(yt_clean, yp_clean), # 유효 응답 정확도
                    'Invalid_Rate': invalid_count_judg / total_judg if total_judg > 0 else 0, # 형식 오류율
                    'Precision': p, 'Recall': r, 'F1_Score': f,
                    'Sample_Count': total_judg, # 전체 샘플 수로 변경
                    'Valid_Count': valid_count_judg # 유효 샘플 수 추가
                })
            else:
                 # 유효한 데이터가 하나도 없는 경우
                 results.append({
                    'Model': model_name, 'Type': 'RQ_Judgment', 'Prompt': prompt,
                    'Overall_Accuracy': 0.0,
                    'Valid_Accuracy': 0.0,
                    'Invalid_Rate': 1.0,
                    'Precision': 0.0, 'Recall': 0.0, 'F1_Score': 0.0,
                    'Sample_Count': total_judg,
                    'Valid_Count': 0
                })

            # --- Answer CM ---
            total_ans = len(y_true_ans)
            valid_idx_ans = [i for i, (t, p) in enumerate(zip(y_true_ans, y_pred_ans)) if t in labels_ans and p in labels_ans]

            yt_clean_ans = [y_true_ans[i] for i in valid_idx_ans]
            yp_clean_ans = [y_pred_ans[i] for i in valid_idx_ans]

            valid_count_ans = len(yt_clean_ans)
            invalid_count_ans = total_ans - valid_count_ans

            correct_ans = sum([1 for yt, yp in zip(yt_clean_ans, yp_clean_ans) if yt == yp])
            overall_acc_ans = correct_ans / total_ans if total_ans > 0 else 0

            if valid_idx_ans:
                plot_filename = os.path.join(EACH_PLOT_DIR, f"CM_{model_name}_{q_type}_Answer_{prompt}.png")
                plot_confusion_matrix(yt_clean_ans, yp_clean_ans, labels_ans, f"{model_name} RQ Answer ({prompt.upper()})", plot_filename)

                # Metrics for Answer (Valid Only)
                p, r, f, _ = precision_recall_fscore_support(yt_clean_ans, yp_clean_ans, average='macro', zero_division=0)
                results.append({
                    'Model': model_name, 'Type': 'RQ_Answer', 'Prompt': prompt,
                    'Overall_Accuracy': overall_acc_ans,
                    'Valid_Accuracy': accuracy_score(yt_clean_ans, yp_clean_ans),
                    'Invalid_Rate': invalid_count_ans / total_ans if total_ans > 0 else 0,
                    'Precision': p, 'Recall': r, 'F1_Score': f,
                    'Sample_Count': total_ans,
                    'Valid_Count': valid_count_ans
                })
            else:
                 results.append({
                    'Model': model_name, 'Type': 'RQ_Answer', 'Prompt': prompt,
                    'Overall_Accuracy': 0.0,
                    'Valid_Accuracy': 0.0,
                    'Invalid_Rate': 1.0,
                    'Precision': 0.0, 'Recall': 0.0, 'F1_Score': 0.0,
                    'Sample_Count': total_ans,
                    'Valid_Count': 0
                })

            # RQ는 이미 내부에서 results에 추가했으므로 continue
            continue

        elif 'TFQ' in q_type: # TFQ, TFQ2, TFQ3
            labels = ['T', 'F']
            for _, row in df.iterrows():
                y_true.append(parse_tfq(row['label']))
                y_pred.append(parse_tfq(row[col_ans]))

        else:
            print(f"Unknown type: {q_type}")
            continue

        # 유효하지 않은 데이터('UNKNOWN') 필터링 및 통계 계산
        total_count = len(y_true)
        valid_indices = [i for i, (t, p) in enumerate(zip(y_true, y_pred)) if t in labels and p in labels]

        y_true_clean = [y_true[i] for i in valid_indices]
        y_pred_clean = [y_pred[i] for i in valid_indices]

        valid_count = len(valid_indices)
        invalid_count = total_count - valid_count

        # Overall Accuracy: (유효하고 정답인 개수) / 전체 개수
        correct_count = sum([1 for yt, yp in zip(y_true_clean, y_pred_clean) if yt == yp])
        overall_acc = correct_count / total_count if total_count > 0 else 0

        if not y_true_clean:
            print(f"No valid data for {filename} - {prompt}")
            # 유효 데이터가 없더라도 결과는 기록 (Overall Accuracy = 0)
            results.append({
                'Model': model_name,
                'Type': q_type,
                'Prompt': prompt,
                'Overall_Accuracy': overall_acc,
                'Valid_Accuracy': 0.0,
                'Invalid_Rate': 1.0, # 전부 Invalid
                'Precision': 0.0,
                'Recall': 0.0,
                'F1_Score': 0.0,
                'Sample_Count': total_count,
                'Valid_Count': 0
            })
            continue

        # Confusion Matrix 저장 (유효 데이터 기준) - 개별 파일은 each_plot에 저장
        plot_filename = os.path.join(EACH_PLOT_DIR, f"CM_{model_name}_{q_type}_{prompt}.png")
        plot_confusion_matrix(y_true_clean, y_pred_clean, labels, f"{model_name} {q_type} ({prompt.upper()})", plot_filename)

        # 성능 지표 계산 (유효 데이터 기준)
        valid_acc = accuracy_score(y_true_clean, y_pred_clean)
        # Macro average로 계산
        prec, rec, f1, _ = precision_recall_fscore_support(y_true_clean, y_pred_clean, average='macro', zero_division=0)

        results.append({
            'Model': model_name,
            'Type': q_type,
            'Prompt': prompt,
            'Overall_Accuracy': overall_acc, # 전체 정확도
            'Valid_Accuracy': valid_acc,     # 유효 응답 정확도
            'Invalid_Rate': invalid_count / total_count if total_count > 0 else 0, # 형식 오류율
            'Precision': prec,
            'Recall': rec,
            'F1_Score': f1,
            'Sample_Count': total_count,    # 전체 샘플 수
            'Valid_Count': valid_count      # 유효 샘플 수
        })

    return results

def collect_data_for_aggregated_cm(all_files):
    """통합 Confusion Matrix 생성을 위해 모든 파일에서 데이터 수집"""
    # 문항 유형별로 데이터 수집: MCQ, MAQ, RQ_Judgment, RQ_Answer, TFQ, TFQ2, TFQ3
    data_collection = {
        'MCQ': {'y_true': [], 'y_pred': [], 'labels': ['A', 'B', 'C', 'D']},
        'MAQ': {'y_true': [], 'y_pred': [], 'labels': ['Selected', 'Not Selected']},
        'RQ_Judgment': {'y_true': [], 'y_pred': [], 'labels': ['T', 'F']},
        'RQ_Answer': {'y_true': [], 'y_pred': [], 'labels': ['A', 'B', 'C', 'D']},
        'TFQ': {'y_true': [], 'y_pred': [], 'labels': ['T', 'F']},
        'TFQ2': {'y_true': [], 'y_pred': [], 'labels': ['T', 'F']},
        'TFQ3': {'y_true': [], 'y_pred': [], 'labels': ['T', 'F']},
    }

    for filepath in all_files:
        filename = os.path.basename(filepath)
        parts = filename.replace('.xlsx', '').split('_')
        if len(parts) < 2:
            continue

        model_name = parts[0]
        q_type = parts[1]

        try:
            df = pd.read_excel(filepath)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        for prompt in PROMPTS:
            col_ans = f"{prompt}_ans"
            if col_ans not in df.columns:
                continue

            if q_type == 'MCQ':
                for _, row in df.iterrows():
                    true_val = parse_mcq(row['label'])
                    pred_val = parse_mcq(row[col_ans])
                    if true_val in data_collection['MCQ']['labels'] and pred_val in data_collection['MCQ']['labels']:
                        data_collection['MCQ']['y_true'].append(true_val)
                        data_collection['MCQ']['y_pred'].append(pred_val)

            elif q_type == 'MAQ':
                options = ['A', 'B', 'C', 'D']
                for _, row in df.iterrows():
                    true_set = parse_maq(row['label'])
                    pred_set = parse_maq(row[col_ans])
                    for opt in options:
                        true_val = 'Selected' if opt in true_set else 'Not Selected'
                        pred_val = 'Selected' if opt in pred_set else 'Not Selected'
                        data_collection['MAQ']['y_true'].append(true_val)
                        data_collection['MAQ']['y_pred'].append(pred_val)

            elif q_type == 'RQ':
                # Judgment
                for _, row in df.iterrows():
                    _, t_judg = parse_rq_full(row['label'])
                    _, p_judg = parse_rq_full(row[col_ans])
                    if t_judg in data_collection['RQ_Judgment']['labels'] and p_judg in data_collection['RQ_Judgment']['labels']:
                        data_collection['RQ_Judgment']['y_true'].append(t_judg)
                        data_collection['RQ_Judgment']['y_pred'].append(p_judg)

                # Answer
                for _, row in df.iterrows():
                    t_ans, _ = parse_rq_full(row['label'])
                    p_ans, _ = parse_rq_full(row[col_ans])
                    if t_ans in data_collection['RQ_Answer']['labels'] and p_ans in data_collection['RQ_Answer']['labels']:
                        data_collection['RQ_Answer']['y_true'].append(t_ans)
                        data_collection['RQ_Answer']['y_pred'].append(p_ans)

            elif q_type in ['TFQ', 'TFQ2', 'TFQ3']:
                for _, row in df.iterrows():
                    true_val = parse_tfq(row['label'])
                    pred_val = parse_tfq(row[col_ans])
                    if true_val in data_collection[q_type]['labels'] and pred_val in data_collection[q_type]['labels']:
                        data_collection[q_type]['y_true'].append(true_val)
                        data_collection[q_type]['y_pred'].append(pred_val)

    return data_collection

def create_aggregated_confusion_matrices(data_collection):
    """통합 Confusion Matrix 생성 및 저장"""
    for q_type, data in data_collection.items():
        if not data['y_true']:  # 데이터가 없으면 스킵
            print(f"No data collected for {q_type}, skipping aggregated CM...")
            continue

        # 통합 Confusion Matrix 생성
        plot_filename = os.path.join(RESULT_DIR, f"CM_aggregated_{q_type}.png")
        title = f"Aggregated Confusion Matrix - {q_type}"
        plot_confusion_matrix(data['y_true'], data['y_pred'], data['labels'], title, plot_filename)
        print(f"Created aggregated CM for {q_type}: {len(data['y_true'])} samples")

def main():
    all_files = glob.glob(os.path.join(DATA_DIR, "*_merged.xlsx"))
    all_results = []

    print(f"Found {len(all_files)} files.")

    for filepath in all_files:
        file_results = analyze_file(filepath)
        all_results.extend(file_results)

    # 통합 Confusion Matrix 생성
    print("\nCreating aggregated confusion matrices...")
    data_collection = collect_data_for_aggregated_cm(all_files)
    create_aggregated_confusion_matrices(data_collection)

    # 전체 결과 엑셀 저장 (Model, Type 순서로 정렬)
    if all_results:
        result_df = pd.DataFrame(all_results)
        # Model, Type 순서로 정렬
        result_df = result_df.sort_values(by=['Model', 'Type'], ascending=[True, True])
        result_path = os.path.join(RESULT_DIR, 'overall_performance_metrics.xlsx')
        result_df.to_excel(result_path, index=False)
        print(f"\nAnalysis Complete! Results saved to {result_path}")
        print(f"Individual Confusion Matrix images saved in {EACH_PLOT_DIR}")
        print(f"Aggregated Confusion Matrix images saved in {RESULT_DIR}")
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
