import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set the style for professional academic plots
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'figure.dpi': 300
})

# Data Preparation
# 1. Prompt Strategy Data
prompts = ['CoT', 'CoVe', 'AO']
prompt_scores = [82.17, 81.50, 75.80]

# 2. Model Data
models = ['GPT-4o', 'GPT-4o-mini', 'Llama3-Med42-70B', 'GPT-5', 'Medicine-Chat-7B']
model_scores = [91.00, 85.17, 82.94, 82.61, 57.39]

# 3. Question Type Data
q_types = ['TFQ2', 'MCQ', 'TFQ3', 'RQ', 'TFQ', 'MAQ']
q_type_scores = [89.40, 85.80, 81.80, 80.53, 74.87, 66.53]

# Create Figure and Axes (1 row, 3 columns)
fig, axes = plt.subplots(1, 3, figsize=(20, 6), constrained_layout=True)

# Function to add value labels on top of bars
def add_labels(ax, rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

# Plot 1: Impact of Prompt Strategy
colors_prompt = sns.color_palette("Blues_r", len(prompts))
bars1 = axes[0].bar(prompts, prompt_scores, color=colors_prompt, edgecolor='black', alpha=0.8)
axes[0].set_title('(a) Impact of Prompt Strategy', fontweight='bold', pad=15)
axes[0].set_ylabel('Accuracy (%)')
axes[0].set_ylim(0, 100)
add_labels(axes[0], bars1)

# Plot 2: Model Comparison
colors_model = sns.color_palette("Greens_r", len(models))
bars2 = axes[1].bar(models, model_scores, color=colors_model, edgecolor='black', alpha=0.8)
axes[1].set_title('(b) Model Comparison', fontweight='bold', pad=15)
# Rotate x-labels for better readability
axes[1].tick_params(axis='x', rotation=30)
axes[1].set_ylim(0, 100)
add_labels(axes[1], bars2)

# Plot 3: Performance by Question Type
colors_qtype = sns.color_palette("Purples_r", len(q_types))
bars3 = axes[2].bar(q_types, q_type_scores, color=colors_qtype, edgecolor='black', alpha=0.8)
axes[2].set_title('(c) Performance by Question Type', fontweight='bold', pad=15)
axes[2].set_ylim(0, 100)
add_labels(axes[2], bars3)

# Overall Figure Caption (Optional, usually added in LaTeX/Word, but included here for completeness)
fig.suptitle('Strict accuracy by prompt strategy, model, and question type',
             fontsize=18, fontweight='bold', y=1.05)

# Save the figure
plt.savefig('strict_accuracy.png', bbox_inches='tight', dpi=300)

# Show the plot
# plt.show()
