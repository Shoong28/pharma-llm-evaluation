# 재현 안내

## 1. 실행 환경

분석·API 추론에는 `requirements.txt`, CUDA 기반 로컬 모델 추론에는 `requirements-local-models.txt`를 사용합니다. GPU 메모리와 드라이버에 맞는 PyTorch/bitsandbytes 환경이 필요합니다. Mac CPU 환경에서 4-bit/8-bit GPU 실험을 그대로 재현할 수 있다고 가정하지 않습니다.

API 실행 전에 `.env`를 설정하거나 셸에 `OPENAI_API_KEY`, `HF_TOKEN`을 설정하세요. `.env`를 자동 로드하지 않는 스크립트에는 셸 환경변수가 필요합니다. API 실험에는 사용 요금이 발생합니다. 전체 9,000개 응답 생성은 이번 정리에서 실행하지 않았습니다.

## 2. 원천 데이터와 문항 생성

1. 사용 권한이 있는 DrugBank XML을 준비하고 `data_drug/`의 파싱·분류·결측 분석 코드를 확인합니다. 파일별 상단 입력·출력 경로를 현재 환경에 맞춥니다.
2. `generate_question/`에서 `generate_mcq.ipynb`를 엽니다. 입력은 `filtered_five_or_more_N.jsonl`입니다. 셀을 순서대로 검토하고 생성·정제 단계를 실행합니다.
3. `recognize_and_rewrite_medqa.py`와 `gen_medqa_questions.py`는 MultifacetEval 기반 변환 단계입니다. MedCAT 1.x, 해당 모델 pack, `concept_attributes.json`, `synonyms_of_options.json` 또는 이를 생성할 입력을 준비해야 합니다. 별도 환경에 `requirements-question-transform.txt`를 설치하고 MedCAT 요구사항에 맞춰 의존성을 조정합니다.
4. TFQ2·TFQ3는 `generate_tfq2.py`, `generate_tfq3.py`에 구현되어 있습니다. `generate_question/`에서 실행하며 `SOURCE_FOLDER`, `FILE_LIMIT`, 출력 경로를 먼저 확인하세요. 기본값이 서로 다른 실험 시점을 반영할 수 있습니다. 필요한 `output/` 폴더를 만드세요.
5. 생성 문항은 `generated_ques/`의 정제·선택 코드를 검토해 준비합니다. `select_70_samples.py`는 중간 실험 유틸리티이며 최종 100문항 설계와 동일하다고 가정하지 마세요.

## 3. 응답 생성과 병합

`generate_answer/`에서 해당 노트북을 엽니다.

- `generate_w_gpt.ipynb`: OpenAI 모델 AO/CoT와 CoVe 검증 질문·검증 답·최종 답 생성.
- `generate_w_local_llm.ipynb`: medicine-chat 및 Med42 양자화 추론. 일부 파싱·보조 단계에서 GPT-4.1 API를 사용하므로 완전한 오프라인 파이프라인이 아닙니다.
- `merge_prompts.ipynb`: 프롬프트별 답변 병합.

각 노트북의 `model_names`, `question_type(s)`, `data_path`, `output_path`를 확인합니다. 같은 이름의 함수가 후속 실험 셀에서 재정의되기도 하므로 전체 자동 실행보다 목표 실험에 맞춰 셀 구성을 먼저 확인해야 합니다. 데이터 스키마는 `ques`, `label` 및 유형별 부가 필드를 사용하며 병합 결과는 `label`, `ao_ans`, `cot_ans`, `cove_ans`를 포함합니다.

## 4. 정확도와 유효 응답 평가

직접 준비한 병합 파일을 `evaluation/data/{model}_{type}_merged.xlsx`에 배치합니다. 예: `gpt-4o_MCQ_merged.xlsx`. 모델 5개, 문항 유형 6개이면 30개 입력 파일입니다.

- Strict Accuracy: `evaluation/accuracy_analysis.ipynb`를 `evaluation/` 작업 디렉터리에서 실행합니다.
- 유효 응답 지표 및 혼동행렬: 저장소 루트에서 `python evaluation/analyze_performance.py`를 실행합니다. `PHARMA_DATA_DIR`, `PHARMA_RESULT_DIR` 환경변수로 경로를 변경할 수 있습니다.
- 유효 지표 그래프: `evaluation/plot_valid_metrics.py`는 작업 디렉터리의 `overall_performance_metrics.xlsx`를 읽습니다.
- 보고된 집계 그래프: `reports/plot_reported_results.py`는 하드코딩된 연구 당시 집계를 시각화합니다. 원본 응답을 재계산하지 않습니다.

## 5. 알려진 한계

원래 평가 파서는 MCQ·MAQ에서 문자열 내 A–D 문자를 추출하는 등 느슨한 규칙을 포함합니다. Strict와 Valid 결과를 비교할 때 파서 정의를 함께 확인해야 합니다. 연구 결과의 보존을 위해 이번 정리에서 평가 정의를 새로 바꾸지 않았습니다.

정확도 차이는 이 벤치마크와 당시 설정에 대한 관찰입니다. 모델 제공사의 이후 업데이트, 양자화, API 파라미터, 표본 구성, 파싱 방식에 따라 결과가 달라질 수 있습니다. 임상 의사결정용 검증을 의미하지 않습니다.
