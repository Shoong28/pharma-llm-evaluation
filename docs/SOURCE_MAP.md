# 원본과 정리본의 관계

정리본은 원래 연구 폴더의 파일을 복사해 만들었습니다. 원본 파일은 수정하지 않았습니다. 파일별 원본 상대 경로와 SHA-256은 `source_manifest.json`에 있습니다.

- `data_drug/`, `generate_question/`, `generated_ques/`: 핵심 Python 코드 보존. 모델 자산과 데이터 제외.
- `generate_question/객관식생성.ipynb` → `generate_question/generate_mcq.ipynb`
- `generate_answer/`: 현재 추론·병합 노트북 3개 보존.
- `최종실험정확도/accuracy_analysis.ipynb` → `evaluation/accuracy_analysis.ipynb`
- `analyze_performance.py` → `evaluation/analyze_performance.py`
- `기타/논문/strict.py` → `reports/plot_reported_results.py`
- `기타/논문/valid.py` → `evaluation/plot_valid_metrics.py`

정리본에서 바꾼 사항: 하드코딩 인증키를 환경변수 참조로 교체, 노트북 출력·실행 이력 제거, 평가 스크립트의 데이터·결과 경로 조정, 분석 노트북의 기본 폰트 변경. 중복 원본·구버전·대형 데이터는 제외했습니다. 폴더 구조와 실행 설명, 의존성 목록, 집계 확인 도구는 이번 정리에서 추가했습니다.

파일의 줄바꿈을 LF로 통일하고 줄 끝 공백도 정리했습니다.
