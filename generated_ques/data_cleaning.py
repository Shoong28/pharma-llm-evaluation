'''
    Data cleaning for Excel files
    - Remove rows with missing values in label columns
    - Clean up label columns (remove brackets and quotes)
    - Sort alphabetically for label columns
    - Save cleaned data to new files
'''
import os
import pandas as pd

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe by removing missing values and cleaning label columns
    """
    # Create a copy to avoid modifying the original
    df_clean = df.copy()

    # Remove rows where label is empty list or contains empty values
    df_clean = df_clean[
        (df_clean['label'].astype(str) != '[]') &
        (df_clean['label'].astype(str) != '')
    ]

    # Clean label columns by removing brackets and quotes
    def clean_column_value(value):
        if pd.isna(value):
            return value

        # Convert to string if it's a list
        if isinstance(value, list):
            value = str(value)

        # Remove brackets and quotes, but preserve the structure
        value = str(value).replace('[', '').replace(']', '').replace("'", '').replace('"', '')

        # Split by comma and clean each element
        if ',' in value:
            elements = [elem.strip() for elem in value.split(',') if elem.strip()]
            # Return as comma-separated string for consistency
            return ','.join(elements) if elements else ''
        else:
            return value.strip()

    df_clean['label'] = df_clean['label'].apply(clean_column_value)

    # Remove rows where label is empty after cleaning
    df_clean = df_clean[
        (df_clean['label'].astype(str) != '')
    ]

    # Sort alphabetically for label columns
    def sort_alphabetically(value):
        if pd.isna(value) or value == '':
            return value

        # Split by comma, sort, and join back
        if ',' in str(value):
            elements = [elem.strip() for elem in str(value).split(',') if elem.strip()]
            return ','.join(sorted(elements))
        else:
            return str(value).strip()

    df_clean['label'] = df_clean['label'].apply(sort_alphabetically)

    return df_clean


def clean_excel_file(input_file: str, output_file: str):
    """
    Clean a single Excel file and save the cleaned version
    """
    print(f"Processing {input_file}...")

    # Read the Excel file
    df = pd.read_excel(input_file)
    print(f"Original data shape: {df.shape}")

    # Clean the data
    df_clean = clean_data(df)
    print(f"After cleaning: {df_clean.shape}")

    # Save the cleaned data
    df_clean.to_excel(output_file, index=False)
    print(f"Saved cleaned data: {output_file}")

    return df_clean

def main():
    # Define the Excel files to process
    excel_files = ['MCQ.xlsx', 'MAQ.xlsx', 'RQ.xlsx', 'TFQ.xlsx']

    # Create output directory for cleaned files
    output_dir = 'cleaned'
    os.makedirs(output_dir, exist_ok=True)

    print("=== 데이터 정제 시작 ===")

    for file_name in excel_files:
        if os.path.exists(file_name):
            # Create output filename
            output_file = os.path.join(output_dir, f'cleaned_{file_name}')

            # Clean the file
            clean_excel_file(file_name, output_file)
            print()
        else:
            print(f"Warning: {file_name} not found")

    print("=== 데이터 정제 완료 ===")

if __name__ == '__main__':
    main()
