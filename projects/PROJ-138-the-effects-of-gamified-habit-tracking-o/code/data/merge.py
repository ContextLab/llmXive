import os
import pandas as pd
from code.utils.logging import pipeline_logger
from code.utils.config import set_random_seed

def merge_datasets(
    input_path: str = "data/processed/weekly_aggregated.csv",
    user_profile_path: str = "data/raw/synthetic_data.csv",
    output_path: str = "data/processed/merged_data.csv"
) -> pd.DataFrame:
    """
    Merge weekly aggregated adherence data with user profile data (gamification status, personality scores).
    
    This function performs the final data consolidation required for T017, ensuring the output CSV
    contains all required columns: User_ID, Gamified, Adherence, and Personality Scores.
    
    Args:
        input_path: Path to the weekly aggregated data (output of T014).
        user_profile_path: Path to the raw user profile data (output of T013a).
        output_path: Path where the merged CSV will be written.
    
    Returns:
        The merged DataFrame.
    
    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If required columns are missing or group sizes are insufficient.
    """
    set_random_seed(42)
    logger = pipeline_logger
    logger.info(f"Starting merge process. Input: {input_path}, Profile: {user_profile_path}")

    # 1. Load Aggregated Data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Aggregated data not found at {input_path}. Run T014 first.")
    
    df_agg = pd.read_csv(input_path)
    logger.info(f"Loaded aggregated data: {df_agg.shape}")

    # 2. Load User Profile Data
    if not os.path.exists(user_profile_path):
        raise FileNotFoundError(f"User profile data not found at {user_profile_path}. Run T013a first.")
    
    df_users = pd.read_csv(user_profile_path)
    logger.info(f"Loaded user profile data: {df_users.shape}")

    # 3. Validate Required Columns
    required_agg_cols = ['User_ID', 'week_number', 'weekly_adherence_flag']
    required_user_cols = ['User_ID', 'gamified_status', 'conscientiousness_score', 'need_for_achievement']

    missing_agg = [col for col in required_agg_cols if col not in df_agg.columns]
    missing_user = [col for col in required_user_cols if col not in df_users.columns]

    if missing_agg:
        raise ValueError(f"Missing columns in aggregated data: {missing_agg}")
    if missing_user:
        raise ValueError(f"Missing columns in user profile data: {missing_user}")

    # 4. Perform Merge
    # We merge on User_ID. The aggregated data might have multiple rows per user (one per week).
    # We need to broadcast the user-level attributes (Gamified, Personality) to every row.
    # Select only necessary columns from users to avoid duplicates
    df_users_subset = df_users[required_user_cols].copy()
    
    df_merged = pd.merge(
        df_agg,
        df_users_subset,
        on='User_ID',
        how='inner'
    )

    logger.info(f"Merged data shape: {df_merged.shape}")

    # 5. Rename Columns to Match Spec (User_ID, Gamified, Adherence, Personality Scores)
    # Standardize column names for the final artifact
    rename_map = {
        'gamified_status': 'Gamified',
        'conscientiousness_score': 'Conscientiousness_Score',
        'need_for_achievement': 'Need_for_Achievement',
        'weekly_adherence_flag': 'Adherence'
    }
    df_merged = df_merged.rename(columns=rename_map)

    # Ensure 'Gamified' is boolean/int as expected by downstream modeling
    # The spec implies a binary group indicator
    if df_merged['Gamified'].dtype != bool:
        df_merged['Gamified'] = df_merged['Gamified'].astype(bool)

    # 6. Validate Group Sizes (FR-008: Non-gamified >= 30)
    group_counts = df_merged['Gamified'].value_counts()
    non_gamified_count = group_counts.get(False, 0)
    
    logger.info(f"Group distribution: {dict(group_counts)}")
    
    if non_gamified_count < 30:
        error_msg = f"Group Imbalance: Non-gamified group size ({non_gamified_count}) is less than required 30."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # 7. Write Output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_merged.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote merged data to {output_path}")

    return df_merged

def main():
    """Entry point for the merge script."""
    try:
        merge_datasets()
        print("Merge completed successfully.")
    except Exception as e:
        pipeline_logger.error(f"Merge failed: {e}")
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())