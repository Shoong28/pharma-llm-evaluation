'''
    Select 70 samples from cleaned files, excluding already selected samples from sampled/30/
    - Read cleaned files (MAQ, MCQ, RQ, TFQ)
    - Exclude primary keys that are already selected in sampled/30/
    - Select 70 new samples for each type with balanced distribution
    - Save to sampled/70/ directory

    Primary Keys:
    - MCQ: idx
    - MAQ, RQ: (idx, n_or_p)
    - TFQ: (idx, n_or_p, T_or_F)
'''
import os
import pandas as pd
import random
from typing import Set, List, Tuple

def get_excluded_keys(sampled_30_dir: str) -> dict:
    """
    Get primary keys that are already selected in sampled/30/ directory
    Primary keys differ by data type:
    - MCQ: idx
    - MAQ, RQ: (idx, n_or_p)
    - TFQ: (idx, n_or_p, T_or_F)
    """
    excluded_keys = {}

    file_mapping = {
        'MAQ': 'selected_MAQ.xlsx',
        'MCQ': 'selected_MCQ.xlsx',
        'RQ': 'selected_RQ.xlsx',
        'TFQ': 'selected_TFQ.xlsx'
    }

    for data_type, filename in file_mapping.items():
        file_path = os.path.join(sampled_30_dir, filename)
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)

            if data_type == 'MCQ':
                # MCQ: primary key is idx
                if 'idx' in df.columns:
                    excluded_keys[data_type] = set(df['idx'].tolist())
                    print(f"Found {len(excluded_keys[data_type])} excluded keys for {data_type}: {sorted(excluded_keys[data_type])}")
                else:
                    excluded_keys[data_type] = set()
                    print(f"No 'idx' column found in {filename}")

            elif data_type in ['MAQ', 'RQ']:
                # MAQ, RQ: primary key is (idx, n_or_p)
                if 'idx' in df.columns and 'n_or_p' in df.columns:
                    excluded_keys[data_type] = set(df[['idx', 'n_or_p']].apply(tuple, axis=1).tolist())
                    print(f"Found {len(excluded_keys[data_type])} excluded keys for {data_type}")
                else:
                    excluded_keys[data_type] = set()
                    print(f"Missing required columns in {filename}")

            elif data_type == 'TFQ':
                # TFQ: primary key is (idx, n_or_p, T_or_F)
                if all(col in df.columns for col in ['idx', 'n_or_p', 'T_or_F']):
                    excluded_keys[data_type] = set(df[['idx', 'n_or_p', 'T_or_F']].apply(tuple, axis=1).tolist())
                    print(f"Found {len(excluded_keys[data_type])} excluded keys for {data_type}")
                else:
                    excluded_keys[data_type] = set()
                    print(f"Missing required columns in {filename}")
        else:
            excluded_keys[data_type] = set()
            print(f"File not found: {file_path}")

    return excluded_keys

def select_70_samples(cleaned_file: str, excluded_keys: Set, data_type: str, sample_size: int = 70) -> pd.DataFrame:
    """
    Select 70 samples from cleaned file, excluding already selected keys
    with balanced distribution based on data type
    """
    print(f"\nProcessing {data_type}...")

    # Read cleaned file
    df = pd.read_excel(cleaned_file)
    print(f"Original {data_type} data shape: {df.shape}")

    # Filter out excluded keys based on data type
    if data_type == 'MCQ':
        # MCQ: filter by idx
        df_available = df[~df['idx'].isin(excluded_keys)]
    elif data_type in ['MAQ', 'RQ']:
        # MAQ, RQ: filter by (idx, n_or_p)
        df['_key'] = df[['idx', 'n_or_p']].apply(tuple, axis=1)
        df_available = df[~df['_key'].isin(excluded_keys)]
        df_available = df_available.drop('_key', axis=1)
    elif data_type == 'TFQ':
        # TFQ: filter by (idx, n_or_p, T_or_F)
        df['_key'] = df[['idx', 'n_or_p', 'T_or_F']].apply(tuple, axis=1)
        df_available = df[~df['_key'].isin(excluded_keys)]
        df_available = df_available.drop('_key', axis=1)

    print(f"Available {data_type} data after excluding selected: {df_available.shape}")

    if len(df_available) == 0:
        print(f"Warning: No available data for {data_type} after excluding selected keys")
        return pd.DataFrame()

    # Select samples with balanced distribution
    if data_type == 'MCQ':
        # MCQ: simple random sampling
        if len(df_available) >= sample_size:
            df_selected = df_available.sample(n=sample_size, random_state=42)
            print(f"Selected {sample_size} samples for {data_type}")
        else:
            print(f"Warning: Only {len(df_available)} available samples for {data_type}, using all")
            df_selected = df_available

    elif data_type in ['MAQ', 'RQ']:
        # MAQ, RQ: balanced sampling by n_or_p (35 neg, 35 pos)
        df_selected = pd.DataFrame()
        samples_per_group = sample_size // 2  # 35 each

        for n_or_p_value in ['neg', 'pos']:
            df_group = df_available[df_available['n_or_p'] == n_or_p_value]
            print(f"  Available {n_or_p_value}: {len(df_group)} samples")

            if len(df_group) >= samples_per_group:
                df_group_selected = df_group.sample(n=samples_per_group, random_state=42)
                print(f"  Selected {samples_per_group} {n_or_p_value} samples")
            else:
                print(f"  Warning: Only {len(df_group)} {n_or_p_value} samples available, using all")
                df_group_selected = df_group

            df_selected = pd.concat([df_selected, df_group_selected], ignore_index=True)

    elif data_type == 'TFQ':
        # TFQ: balanced sampling by (n_or_p, T_or_F) combinations
        # 4 combinations: (neg, T), (neg, F), (pos, T), (pos, F)
        # Each should have ~17-18 samples (70/4 = 17.5)
        df_selected = pd.DataFrame()
        samples_per_group = sample_size // 4  # 17
        remaining = sample_size % 4  # 2 (to make 70 total)

        combinations = [
            ('neg', 'T'), ('neg', 'F'), ('pos', 'T'), ('pos', 'F')
        ]

        for i, (n_or_p_value, t_or_f_value) in enumerate(combinations):
            df_group = df_available[
                (df_available['n_or_p'] == n_or_p_value) &
                (df_available['T_or_F'] == t_or_f_value)
            ]
            print(f"  Available ({n_or_p_value}, {t_or_f_value}): {len(df_group)} samples")

            # Distribute remaining samples to first groups
            n_samples = samples_per_group + (1 if i < remaining else 0)

            if len(df_group) >= n_samples:
                df_group_selected = df_group.sample(n=n_samples, random_state=42)
                print(f"  Selected {n_samples} ({n_or_p_value}, {t_or_f_value}) samples")
            else:
                print(f"  Warning: Only {len(df_group)} ({n_or_p_value}, {t_or_f_value}) samples available, using all")
                df_group_selected = df_group

            df_selected = pd.concat([df_selected, df_group_selected], ignore_index=True)

    print(f"Total selected samples: {len(df_selected)}")

    return df_selected

def main():
    # Set random seed for reproducibility
    random.seed(42)

    # Define paths
    # cleaned_dir = ''
    sampled_30_dir = 'sampled/30'
    sampled_70_dir = 'sampled/70'

    # Create output directory
    os.makedirs(sampled_70_dir, exist_ok=True)

    # Get excluded primary keys from sampled/30/
    print("=== Getting excluded primary keys from sampled/30/ ===")
    excluded_keys = get_excluded_keys(sampled_30_dir)

    # Process each data type
    file_mapping = {
        'MAQ': 'MAQ.xlsx',
        'MCQ': 'MCQ.xlsx',
        'RQ': 'RQ.xlsx',
        'TFQ': 'TFQ.xlsx'
    }

    print("\n=== Selecting 70 samples for each type with balanced distribution ===")
    for data_type, filename in file_mapping.items():
        cleaned_file = os.path.join(filename)

        if os.path.exists(cleaned_file):
            # Select 70 samples with balanced distribution
            df_selected = select_70_samples(cleaned_file, excluded_keys[data_type], data_type)

            if not df_selected.empty:
                # Save to sampled/70/
                output_file = os.path.join(sampled_70_dir, f'selected_{data_type}.xlsx')
                df_selected.to_excel(output_file, index=False)
                print(f"Saved {data_type} samples to: {output_file}")

                # Print distribution summary
                if data_type in ['MAQ', 'RQ']:
                    n_or_p_counts = df_selected['n_or_p'].value_counts()
                    print(f"  Distribution - neg: {n_or_p_counts.get('neg', 0)}, pos: {n_or_p_counts.get('pos', 0)}")
                elif data_type == 'TFQ':
                    combo_counts = df_selected.groupby(['n_or_p', 'T_or_F']).size()
                    print(f"  Distribution:")
                    for (n_or_p, t_or_f), count in combo_counts.items():
                        print(f"    ({n_or_p}, {t_or_f}): {count}")
            else:
                print(f"No samples selected for {data_type}")
        else:
            print(f"Cleaned file not found: {cleaned_file}")

    print("\n=== Selection completed ===")

if __name__ == '__main__':
    main()
