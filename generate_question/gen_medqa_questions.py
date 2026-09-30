'''
    generating MAQ,TFQ,RQ questions from the original 800 matched USMLE questions
'''
from medcat.cat import CAT
import json
import random
import copy
import os
from itertools import product
import numpy as np
random.seed(48)

# 현재 스크립트의 디렉토리를 기준으로 모델 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'models', 'umls_sm_pt2ch_533bab5115c6c2d6.zip')

# 모델 로딩 시도
try:
    print(f"모델 로딩 시도: {model_path}")
    cat = CAT.load_model_pack(model_path)
    print("모델 로딩 성공!")
except Exception as e:
    print(f"모델 로딩 실패: {e}")
    print("대안 모델 시도...")
    try:
        # 대안 모델 경로 시도
        alt_model_path = os.path.join(script_dir, 'models', 'medmen_wstatus_2021_oct.zip')
        print(f"대안 모델 로딩 시도: {alt_model_path}")
        cat = CAT.load_model_pack(alt_model_path)
        print("대안 모델 로딩 성공!")
    except Exception as e2:
        print(f"대안 모델도 로딩 실패: {e2}")
        raise Exception("사용 가능한 MedCAT 모델을 찾을 수 없습니다.")

# concept_attributes.json 파일 경로도 수정
concept_attributes_path = os.path.join(script_dir, 'concept_attributes.json')
try:
    synonyms = json.load(open(concept_attributes_path, 'r', encoding='utf-8'))
except UnicodeDecodeError:
    # UTF-8로 읽기 실패 시 다른 인코딩 시도
    try:
        synonyms = json.load(open(concept_attributes_path, 'r', encoding='cp949'))
    except UnicodeDecodeError:
        # 마지막으로 latin-1 인코딩 시도
        synonyms = json.load(open(concept_attributes_path, 'r', encoding='latin-1'))

def get_synonym(text, entities):
    '''
        get synonym of the given sentence
    '''
    all_list = []
    original = []
    for key in entities['entities']:
        item = entities['entities'][key]
        try:
            cui = item['cui']
            syms = synonyms[cui]
            new_syms = [item['source_value']]
            tmp = [item['source_value'].lower()]
            assert item['source_value'] in text
            for one in syms:
                if one.lower() not in tmp:
                    new_syms += [one]
                    tmp += [one.lower()]
            syms = new_syms
        except:
            continue
        detected_name = item['source_value'].lower()
        while '~' in detected_name:
            detected_name = detected_name.replace('~',' ')
        new_other_syms = []
        for one in syms:
            if ',' not in one and '+' not in one and '>' not in one:
                new_other_syms.append(one)
        other_syms = new_other_syms
        all_list.append(other_syms)
        # sym = random.choice(other_syms).lower()
        original.append(item['source_value'])
        # assert item['']
        # text = text.lower().replace(detected_name, sym).capitalize()
    if len(original) == 0:
        return [text]
    all_combs = list(product(*all_list))
    all_texts = []
    sorted_ids = np.argsort([-len(one) for one in original])

    for comb in all_combs:
        new_text = copy.deepcopy(text)
        for i in sorted_ids:
            # if original[i] not in new_text:
            #     print('{}\t{}'.format(new_text, original[i]))
            new_text = new_text.replace(original[i], comb[i])
        new_text = new_text.capitalize()
        all_texts.append(new_text)
    return all_texts

import copy
from tqdm import tqdm
# rewrite.jsonl 파일 경로를 절대 경로로 수정
path = os.path.join(script_dir, 'output', 'rewrite.jsonl')
# valid_keys = ['Disease or Syndrome','']
# out_data = {}
# processed_count = 0
# total_lines = 0

# 이미 생성된 synonyms_of_options.json 파일을 사용
print("기존 synonyms_of_options.json 파일 사용...")
try:
    with open('synonyms_of_options.json', 'r', encoding='utf-8') as f:
        out_data = json.load(f)
    print(f"synonyms_of_options.json 로딩 완료! 키 개수: {len(out_data)}")
except Exception as e:
    print(f"synonyms_of_options.json 로딩 실패: {e}")
    print("파일을 새로 생성합니다...")

    # 파일이 없거나 오류가 발생한 경우에만 새로 생성
    out_data = {}
    processed_count = 0
    total_lines = 0

    try:
        # 먼저 총 줄 수 계산
        with open(path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        print(f"총 {total_lines}줄 처리 시작...")

        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(tqdm(f, total=total_lines)):
                try:
                    entry = json.loads(line.strip())
                    options = entry['options']
                    # Test it
                    answer = entry['answer']
                    answer_text = options[answer]
                    answer_before = copy.deepcopy(answer_text)

                    entities = cat.get_entities(answer_text)
                    answer_texts = get_synonym(answer_before, entities)
                    out_data[answer_text] = answer_texts
                    processed_count += 1

                    # 100줄마다 진행 상황 출력 및 임시 저장
                    if processed_count % 100 == 0:
                        print(f"진행 상황: {processed_count}/{total_lines} 줄 처리 완료")
                        # 임시 파일로 저장
                        temp_file = f'synonyms_of_options_temp_{processed_count}.json'
                        json.dump(out_data, open(temp_file, 'w', encoding='utf-8'), indent=4)
                        print(f"임시 저장 완료: {temp_file}")

                except Exception as e:
                    print(f"줄 {line_num + 1} 처리 중 오류 발생: {e}")
                    print(f"문제가 된 줄: {line[:100]}...")
                    continue  # 오류가 발생해도 계속 진행

        print(f"전체 처리 완료! 총 {processed_count}개 항목 처리됨")
        json.dump(out_data, open('synonyms_of_options.json', 'w', encoding='utf-8'), indent=4)
        print("synonyms_of_options.json 최종 저장 완료!")

    except Exception as e:
        print(f"전체 처리 중 오류 발생: {e}")
        print(f"지금까지 처리된 {processed_count}개 항목 저장 중...")
        # 오류가 발생해도 지금까지의 결과 저장
        if processed_count > 0:
            json.dump(out_data, open('synonyms_of_options_partial.json', 'w', encoding='utf-8'), indent=4)
            print("synonyms_of_options_partial.json 저장 완료!")
        import traceback
        traceback.print_exc()

# Download the model_pack from the models section in the github repo.
# cat = CAT.load_model_pack('/home/zhouyx/medcat/umls_self_train_model_pt2ch_3760d588371755d0.zip')
# concept_types = json.load(open('concept_semantic_types.json','r'))
# synonym = json.load(open('concept_attributes.json','r'))
# rewrite.jsonl 파일 경로를 절대 경로로 수정
path = os.path.join(script_dir, 'output', 'rewrite.jsonl')
mcq_data, mcq_dev_data, maq_data, maq_dev_data, tfq_data,\
      tfq_dev_data, fib_data, fib_dev_data, tfq_2_data, tfq_2_dev_data, ar_dev_data, ar_data = [], [],[],[],[],[],[],[],[],[],[],[]
all_data = []

print("두 번째 단계 시작: rewrite.jsonl 파일 읽기...")
try:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            all_data.append(entry)
    print(f"rewrite.jsonl 파일 읽기 완료! 총 {len(all_data)}개 항목")
except Exception as e:
    print(f"rewrite.jsonl 파일 읽기 실패: {e}")
    raise

print("synonyms_of_options.json 파일 읽기 시작...")
try:
    synonyms_options = json.load(open('synonyms_of_options.json', 'r', encoding='utf-8'))
    print(f"synonyms_of_options.json 읽기 완료! 키 개수: {len(synonyms_options)}")
except Exception as e:
    print(f"synonyms_of_options.json 읽기 실패: {e}")
    raise

print("데이터 처리 시작...")
random.shuffle(all_data)
processed_count = 0

for i, entry in enumerate(all_data):
    try:
        options = entry['options']
        # Test it
        answer = entry['answer']
        answer_text = options[answer]

        # synonyms_options에 answer_text가 없는 경우 처리
        if answer_text not in synonyms_options:
            print(f"경고: '{answer_text[:50]}...'에 대한 동의어를 찾을 수 없습니다. 원본 텍스트 사용.")
            same_meaning_options = [answer_text]  # 원본 텍스트만 사용
        else:
            same_meaning_options = synonyms_options[answer_text]

        # original_ques:
        mcq_ques = 'Question: ' + entry['ques']
        options_text = ['{}: {}'.format(key, options[key]) for key in options]
        mcq_ques += '\n' + 'Options: '+'\t'.join(options_text)
        # MAQ
        corr_num = random.randint(1, 4)
        # 실제 options에 존재하는 키만 사용
        available_options = list(options.keys())
        other_ans = list(set(available_options) - {answer})
        corr_ans = [answer]
        new_options = copy.deepcopy(options)
        if corr_num > 1:
            # same_meaning_options가 비어있거나 너무 적을 때 안전하게 처리
            if len(same_meaning_options) >= corr_num-1:
                same_meaning_options = random.sample(same_meaning_options, k=corr_num-1)
            elif len(same_meaning_options) > 0:
                # 필요한 개수만큼 복제하여 확장
                needed_count = corr_num - 1
                extended_options = []
                while len(extended_options) < needed_count:
                    extended_options.extend(same_meaning_options)
                same_meaning_options = extended_options[:needed_count]
            else:
                # same_meaning_options가 비어있으면 빈 리스트로 설정
                same_meaning_options = []

            # other_corr가 비어있지 않은지 확인
            if len(other_ans) >= corr_num - 1:
                other_corr = random.sample(other_ans, k=corr_num-1)
            else:
                # other_ans가 부족하면 사용 가능한 만큼만 사용
                other_corr = other_ans.copy()
                corr_num = len(other_corr) + 1  # corr_num 조정

            corr_ans += other_corr
            # same_meaning_options와 other_corr의 길이가 맞는지 확인
            for j, one in enumerate(other_corr):
                if j < len(same_meaning_options):
                    new_options[one] = same_meaning_options[j]
                else:
                    # 부족한 경우 원본 텍스트 사용
                    new_options[one] = options[one]

        maq_ques = 'Question: '+entry['maq_ques']
        neg_maq_ques = 'Question: '+entry['neg_maq_ques']
        new_options_text = ['{}: {}'.format(key, new_options[key]) for key in new_options]
        maq_ques += '\n' + 'Options: '+ '\n'.join(new_options_text)
        neg_maq_ques += '\n' + 'Options: '+ '\n'.join(new_options_text)
        maq_ans = corr_ans
        neg_maq_ans = list(set(available_options) - set(corr_ans))
        corr_ans.sort()
        neg_maq_ans.sort()
        other = random.choice(other_ans)
        other_text = options[other]
        ar_ques_p = mcq_ques + '. Alice\'s answer: {}. Please determine whether her answer is correct, and if it\'s incorrect, provide the correct answer.'.format(answer)
        ar_ques_n = mcq_ques + '. Alice\'s answer: {}. Please determine whether her answer is correct, and if it\'s incorrect, provide the correct answer.'.format(other)
        # tfq
        tfq_p = 'Question: '+entry['tfq_ques'].replace('[option_text]', answer_text)
        neg_tfq_n = 'Question: '+entry['neg_tfq_ques'].replace('[option_text]', answer_text)
        tfq_n = 'Question: '+entry['tfq_ques'].replace('[option_text]', other_text)
        neg_tfq_p = 'Question: '+entry['neg_tfq_ques'].replace('[option_text]', other_text)
        if i <5:
            one = random.choice([[i,tfq_p,neg_tfq_n,'T','F'],[i,tfq_n,neg_tfq_p,'F','T']])
            one_2 = random.choice([[i, ar_ques_p, ['T',answer]],[i, ar_ques_n,['F',answer]]])
            tfq_dev_data.append(one)
            mcq_dev_data.append([i, mcq_ques, answer])
            maq_dev_data.append([i, maq_ques, neg_maq_ques, list(corr_ans), list(neg_maq_ans)])
            ar_dev_data.append(one_2)
        else:
            tfq_data.append([i, tfq_p, neg_tfq_n, tfq_n, neg_tfq_p,  'T','F','F','T'])
            mcq_data.append([i, mcq_ques, answer])
            maq_data.append([i, maq_ques, neg_maq_ques, list(corr_ans), list(neg_maq_ans)])
            ar_data.append([i, ar_ques_p, ar_ques_n, ['T',answer], ['F',answer]])

        processed_count += 1
        if processed_count % 100 == 0:
            print(f"진행 상황: {processed_count}/{len(all_data)} 항목 처리 완료")

    except Exception as e:
        print(f"항목 {i} 처리 중 오류 발생: {e}")
        print(f"문제가 된 항목: {entry.get('ques', 'N/A')[:100]}...")
        continue  # 오류가 발생해도 계속 진행

print(f"데이터 처리 완료! 총 {processed_count}개 항목 처리됨")

# 최종 출력 파일 생성
print("최종 출력 파일 생성 시작...")
try:
    # medqa 디렉토리 생성
    for name in ['TFQ','MCQ','MAQ','RQ']:
        dir_path = os.path.join(script_dir, 'medqa', name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"디렉토리 생성: {dir_path}")

    # 각 데이터 타입별로 파일 저장
    print("TFQ 파일 저장 중...")
    json.dump(tfq_dev_data, open(os.path.join(script_dir, 'medqa', 'TFQ', 'dev.json'), 'w', encoding='utf-8'), indent=4)
    json.dump(tfq_data, open(os.path.join(script_dir, 'medqa', 'TFQ', 'test.json'), 'w', encoding='utf-8'), indent=4)
    print(f"TFQ 파일 저장 완료 - dev: {len(tfq_dev_data)}개, test: {len(tfq_data)}개")

    print("MCQ 파일 저장 중...")
    json.dump(mcq_dev_data, open(os.path.join(script_dir, 'medqa', 'MCQ', 'dev.json'), 'w', encoding='utf-8'), indent=4)
    json.dump(mcq_data, open(os.path.join(script_dir, 'medqa', 'MCQ', 'test.json'), 'w', encoding='utf-8'), indent=4)
    print(f"MCQ 파일 저장 완료 - dev: {len(mcq_dev_data)}개, test: {len(mcq_data)}개")

    print("MAQ 파일 저장 중...")
    json.dump(maq_dev_data, open(os.path.join(script_dir, 'medqa', 'MAQ', 'dev.json'), 'w', encoding='utf-8'), indent=4)
    json.dump(maq_data, open(os.path.join(script_dir, 'medqa', 'MAQ', 'test.json'), 'w', encoding='utf-8'), indent=4)
    print(f"MAQ 파일 저장 완료 - dev: {len(maq_dev_data)}개, test: {len(maq_data)}개")

    print("RQ 파일 저장 중...")
    json.dump(ar_dev_data, open(os.path.join(script_dir, 'medqa', 'RQ', 'dev.json'), 'w', encoding='utf-8'), indent=4)
    json.dump(ar_data, open(os.path.join(script_dir, 'medqa', 'RQ', 'test.json'), 'w', encoding='utf-8'), indent=4)
    print(f"RQ 파일 저장 완료 - dev: {len(ar_dev_data)}개, test: {len(ar_data)}개")

    print("모든 출력 파일 생성 완료!")
    print(f"생성된 파일들:")
    print(f"- TFQ: dev.json ({len(tfq_dev_data)}개), test.json ({len(tfq_data)}개)")
    print(f"- MCQ: dev.json ({len(mcq_dev_data)}개), test.json ({len(mcq_data)}개)")
    print(f"- MAQ: dev.json ({len(maq_dev_data)}개), test.json ({len(maq_data)}개)")
    print(f"- RQ: dev.json ({len(ar_dev_data)}개), test.json ({len(ar_data)}개)")

except Exception as e:
    print(f"출력 파일 생성 중 오류 발생: {e}")
    import traceback
    traceback.print_exc()

    # 부분적으로라도 저장 시도
    try:
        print("부분 저장 시도...")
        if len(tfq_dev_data) > 0:
            json.dump(tfq_dev_data, open('tfq_dev_partial.json', 'w', encoding='utf-8'), indent=4)
            print("tfq_dev_partial.json 저장 완료")
        if len(tfq_data) > 0:
            json.dump(tfq_data, open('tfq_test_partial.json', 'w', encoding='utf-8'), indent=4)
            print("tfq_test_partial.json 저장 완료")
        if len(mcq_dev_data) > 0:
            json.dump(mcq_dev_data, open('mcq_dev_partial.json', 'w', encoding='utf-8'), indent=4)
            print("mcq_dev_partial.json 저장 완료")
        if len(mcq_data) > 0:
            json.dump(mcq_data, open('mcq_test_partial.json', 'w', encoding='utf-8'), indent=4)
            print("mcq_test_partial.json 저장 완료")
        if len(maq_dev_data) > 0:
            json.dump(maq_dev_data, open('maq_dev_partial.json', 'w', encoding='utf-8'), indent=4)
            print("maq_dev_partial.json 저장 완료")
        if len(maq_data) > 0:
            json.dump(maq_data, open('maq_test_partial.json', 'w', encoding='utf-8'), indent=4)
            print("maq_test_partial.json 저장 완료")
        if len(ar_dev_data) > 0:
            json.dump(ar_dev_data, open('ar_dev_partial.json', 'w', encoding='utf-8'), indent=4)
            print("ar_dev_partial.json 저장 완료")
        if len(ar_data) > 0:
            json.dump(ar_data, open('ar_test_partial.json', 'w', encoding='utf-8'), indent=4)
            print("ar_test_partial.json 저장 완료")
    except Exception as e2:
        print(f"부분 저장도 실패: {e2}")
