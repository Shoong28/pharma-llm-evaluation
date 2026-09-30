import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 로드 (업로드된 파일명 사용)
df = pd.read_excel('overall_performance_metrics.xlsx')
df['Model'] = df['Model'].replace({'medichat': 'medicine-chat'})

# 스타일 설정
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'serif'

# ==========================================
# 1. Table 2: Valid Metrics Summary (데이터 출력용)
# ==========================================
summary_df = df.groupby('Model')[['Precision', 'Recall', 'F1_Score']].mean().reset_index()
summary_df = summary_df.sort_values('F1_Score', ascending=False)
print("=== [Table 2] Valid Metrics Summary ===")
print(summary_df.round(4))

# ==========================================
# 2. Figure 2: Heatmap (Model vs Question Type F1-Score)
# ==========================================
# 모델별, 문항 유형별 F1 점수 평균 계산
heatmap_data = df.groupby(['Model', 'Type'])['F1_Score'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='Model', columns='Type', values='F1_Score')
# 모델 순서를 성능순으로 정렬
heatmap_pivot = heatmap_pivot.reindex(summary_df['Model'])

plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_pivot, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=.5)
plt.title('Average F1-Score by Model and Question Type', fontsize=14, pad=20)
plt.ylabel('Model')
plt.xlabel('Question Type')
plt.xticks(rotation=45)  # 라벨 기울기 조정
plt.tight_layout()
plt.savefig('figure2_heatmap.png', dpi=300)
# plt.show()

# ==========================================
# 3. Figure 3: RQ Analysis (Judgment vs Answer)
# ==========================================
# RQ 관련 데이터만 필터링
rq_df = df[df['Type'].isin(['RQ_Judgment', 'RQ_Answer'])]
rq_pivot = rq_df.groupby(['Model', 'Type'])['F1_Score'].mean().unstack()
# 모델 순서 정렬
rq_pivot = rq_pivot.reindex(summary_df['Model'])

# 막대 그래프 그리기
ax = rq_pivot.plot(kind='bar', figsize=(10, 6), width=0.7, color=['#7fbf7b', '#af8dc3']) # 색상 예시 (녹색/보라)
plt.title('RQ Analysis: Judgment vs Answer (F1-Score)', fontsize=14, pad=20)
plt.ylabel('F1-Score')
plt.xlabel('Model')
plt.ylim(0, 1.1)
plt.legend(title='Sub-task', labels=['Correct Answer Selection (Answer)', 'Error Detection (Judgment)'], loc='lower right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(rotation=45)


# 값 표시
for p in ax.patches:
    ax.annotate(f'{p.get_height():.2f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', xytext=(0, 5), textcoords='offset points', fontsize=12)

plt.tight_layout()
plt.savefig('figure3_rq_analysis.png', dpi=300)
# plt.show()
