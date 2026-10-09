import pandas as pd
import numpy as np
import os
import logging
import json
from typing import Optional, Tuple, List
from config import get_path

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions for raw-data cleaning (T007)
# ----------------------------------------------------------------------
def _detect_column(df: pd.DataFrame, candidates: List[str]) -> str:
    """
    Return the first column name in the DataFrame that matches any of the
    candidate names (case‑insensitive). Raises a ValueError if none match.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        cand_l = cand.lower()
        if cand_l in lower_cols:
            return lower_cols[cand_l]
    raise ValueError(f"Required column not found. Expected one of {candidates}")

def clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    T007 core cleaning:
    1. Drop duplicate rows.
    2. Drop rows where reaction time or mood rating are missing.
    The function is tolerant to column‑name variations used elsewhere in the
    project (e.g., 'Reaction Time' vs 'reaction_time', 'Mood' vs
    'mood_rating').
    """
    logger.info("Dropping duplicate rows...")
    df = df.drop_duplicates()

    # Identify the reaction‑time and mood columns (case‑insensitive)
    rt_col = _detect_column(df, ["Reaction Time", "reaction_time", "rt"])
    mood_col = _detect_column(df, ["Mood", "mood_rating", "mood"])

    logger.info(f"Using reaction‑time column '{rt_col}' and mood column '{mood_col}'")
    logger.info("Dropping rows with missing reaction time or mood rating...")
    df = df.dropna(subset=[rt_col, mood_col])

    return df

# ----------------------------------------------------------------------
# Legacy helpers (kept for backward compatibility)
# ----------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw dataset: handle missing values, strip whitespace,
    and ensure consistent data types for numerical columns.
    """
    logger.info("Cleaning data (legacy function)...")
    df = df.dropna(subset=['Participant', 'Condition', 'Reaction Time', 'Mood'])

    # Ensure numerical columns are numeric
    numeric_cols = ['Reaction Time', 'Mood']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where numerical conversion failed
    df = df.dropna(subset=numeric_cols)

    return df

# ----------------------------------------------------------------------
# New preprocessing steps required for T008
# ----------------------------------------------------------------------
def _flag_outliers_iqr(df: pd.DataFrame,
                       condition_col: str,
                       rt_col: str,
                       k: float = 1.5) -> pd.DataFrame:
    """
    Compute the IQR of ``rt_col`` within each ``condition_col`` group,
    flag rows whose reaction time lies outside ``k * IQR`` bounds and
    add a boolean column ``is_outlier``.
    """
    logger.info("Flagging outliers using IQR per condition (raw reaction times)...")
    df = df.copy()

    def outlier_mask(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - k * iqr
        upper = q3 + k * iqr
        return (group < lower) | (group > upper)

    df["is_outlier"] = df.groupby(condition_col)[rt_col].transform(outlier_mask)
    return df

def _zscore_normalize(df: pd.DataFrame,
                      condition_col: str,
                      rt_col: str) -> pd.DataFrame:
    """
    Z‑score normalize ``rt_col`` within each ``condition_col`` group.
    The normalized values overwrite the original ``rt_col`` column.
    """
    logger.info("Z‑score normalizing reaction times per condition...")
    df = df.copy()

    def normalize(group):
        mean = group.mean()
        std = group.std()
        if std == 0 or np.isnan(std):
            return pd.Series(0.0, index=group.index)
        return (group - mean) / std

    df[rt_col] = df.groupby(condition_col)[rt_col].transform(normalize)
    return df

# ----------------------------------------------------------------------
# Existing preprocessing pipeline (retained for later steps)
# ----------------------------------------------------------------------
def normalize_rt(df: pd.DataFrame, group_col: str = 'Condition') -> pd.DataFrame:
    """
    Normalize reaction times within each group (Condition).
    Uses Z-score normalization.
    """
    logger.info("Normalizing reaction times...")
    df = df.copy()

    def z_normalize(group):
        mean = group.mean()
        std = group.std()
        if std == 0:
            return pd.Series(0.0, index=group.index)
        return (group - mean) / std

    df['Normalized RT'] = df.groupby(group_col)['Reaction Time'].transform(z_normalize)
    return df

def detect_outliers_iqr(df: pd.DataFrame, group_col: str = 'Condition',
                        rt_col: str = 'Normalized RT', k: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using the Interquartile Range (IQR) method.
    Calculates IQR thresholds PER group (Condition).
    Marks rows as outliers but does NOT remove them.
    """
    logger.info("Detecting outliers using IQR method per Condition...")
    df = df.copy()

    def calculate_outlier_flag(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr

        outliers = (group < lower_bound) | (group > upper_bound)
        return outliers

    df['is_outlier'] = df.groupby(group_col)[rt_col].transform(calculate_outlier_flag)
    return df

def normalize_and_flag_outliers(df: pd.DataFrame, group_col: str = 'Condition', k: float = 1.5) -> pd.DataFrame:
    """
    Combined pipeline: Normalize RTs, then flag outliers using IQR per group.
    """
    df = normalize_rt(df, group_col)
    df = detect_outliers_iqr(df, group_col, rt_col='Normalized RT', k=k)
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract summary features: mean RT and avg mood per participant/condition.
    """
    logger.info("Extracting features...")
    features = df.groupby(['Participant', 'Condition']).agg({
        'Reaction Time': 'mean',
        'Mood': 'mean',
        'is_outlier': 'sum'  # Count outliers per group
    }).reset_index()

    features.columns = ['Participant', 'Condition', 'mean_rt', 'avg_mood', 'outlier_count']
    return features

def save_preprocessed_data(df: pd.DataFrame, design_type: str, output_path: str):
    """
    Save the preprocessed dataframe to CSV.
    """
    logger.info(f"Saving preprocessed data to {output_path}")
    df.to_csv(output_path, index=False)

def log_outlier_removal(df: pd.DataFrame, group_col: str = 'Condition',
                        rt_col: str = 'Normalized RT', output_path: str = None) -> dict:
    """
    Implement T042: Outlier Audit Trail.
    Writes a JSON log containing the count of FLAGGED rows per condition
    and the specific IQR thresholds used.

    Schema: {condition: str, flagged_count: int, iqr_threshold: float}
    Note: 'iqr_threshold' here represents the actual IQR value (Q3‑Q1) used
    to calculate the bounds (Lower=Q1‑1.5*IQR, Upper=Q3+1.5*IQR).
    """
    logger.info("Generating outlier audit trail...")

    if output_path is None:
        output_path = get_path('interim')
        output_path = os.path.join(output_path, 'outlier_log.json')

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    audit_log = []

    # Ensure the outlier column exists
    if 'is_outlier' not in df.columns:
        raise ValueError("Column 'is_outlier' not found. Run normalize_and_flag_outliers first.")

    groups = df[group_col].unique()

    for condition in groups:
        group_data = df[df[group_col] == condition]
        rt_values = group_data[rt_col]

        if len(rt_values) == 0:
            continue

        q1 = rt_values.quantile(0.25)
        q3 = rt_values.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        flagged_count = int(group_data['is_outlier'].sum())

        log_entry = {
            "condition": str(condition),
            "flagged_count": flagged_count,
            "iqr_threshold": float(iqr),
            "q1": float(q1),
            "q3": float(q3),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound)
        }
        audit_log.append(log_entry)

    # Write to file
    with open(output_path, "w") as f:
        json.dump(audit_log, f, indent=2)

    logger.info(f"Outlier audit trail written to {output_path}")
    return audit_log

# ----------------------------------------------------------------------
# New helper for T009 – feature aggregation
# ----------------------------------------------------------------------
def _aggregate_features(df: pd.DataFrame,
                       participant_col: str,
                       condition_col: str,
                       rt_col: str,
                       mood_col: str) -> pd.DataFrame:
    """
    For each participant × condition, compute:
    - mean normalized reaction time (mean_rt)
    - mean mood rating (avg_mood)
    Returns a DataFrame with columns:
    participant_id, condition, mean_rt, avg_mood
    """
    logger.info("Aggregating features for rejection dataset (T009)...")
    agg_df = df.groupby([participant_col, condition_col]).agg({
        rt_col: 'mean',
        mood_col: 'mean'
    }).reset_index()
    agg_df = agg_df.rename(columns={
        participant_col: 'participant_id',
        condition_col: 'condition',
        rt_col: 'mean_rt',
        mood_col: 'avg_mood'
    })
    return agg_df

def _save_features(df_features: pd.DataFrame, output_path: str):
    """
    Persist the aggregated features to CSV.
    """
    logger.info(f"Saving aggregated features to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_features.to_csv(output_path, index=False)

# ----------------------------------------------------------------------
# Main pipeline execution for User Story 2.
# ----------------------------------------------------------------------
def run_preprocessing(input_path: str, output_path: str, design_type: str):
    """
    Main pipeline execution for User Story 2.
    Supports two modes:
    1. Directory mode (T007) – clean each raw CSV and write cleaned files to
       data/interim/cleaned_<dataset_id>.csv.
    2. File mode – perform the full preprocessing pipeline (normalization,
       outlier detection, feature extraction) and write the final preprocessed
       CSV to the supplied output_path.
    """
    logger.info(f"Starting preprocessing pipeline for {input_path}")

    if os.path.isdir(input_path):
        # ------------------------------------------------------------------
        # T007 – directory mode
        # ------------------------------------------------------------------
        interim_dir = get_path('interim')
        os.makedirs(interim_dir, exist_ok=True)

        csv_files = [f for f in os.listdir(input_path) if f.lower().endswith('.csv')]
        if not csv_files:
            logger.warning(f"No CSV files found in directory: {input_path}. "
                           "Skipping cleaning step as there are no raw CSVs to process.")
            # Gracefully exit without raising an exception; downstream steps
            # that depend on cleaned files should handle the absence appropriately.
            return

        for fname in csv_files:
            file_path = os.path.join(input_path, fname)
            logger.info(f"Processing raw file {file_path}")
            df_raw = pd.read_csv(file_path)

            # Apply the T007 cleaning steps
            df_clean = clean_raw_data(df_raw)

            dataset_id = os.path.splitext(fname)[0]  # filename without extension
            cleaned_path = os.path.join(interim_dir, f"cleaned_{dataset_id}.csv")
            df_clean.to_csv(cleaned_path, index=False)
            logger.info(f"Cleaned data written to {cleaned_path}")

        logger.info("All raw files have been cleaned. Exiting directory mode.")
        return  # Directory mode complete; do not continue to full pipeline

    # ------------------------------------------------------------------
    # File mode – new T008 implementation
    # ------------------------------------------------------------------
    # Load data
    df = pd.read_csv(input_path)

    # 1. Core cleaning (duplicate removal & missing RT/mood)
    df = clean_raw_data(df)

    # Determine column names (case‑insensitive)
    condition_col = _detect_column(df, ["Condition", "condition"])
    rt_col = _detect_column(df, ["Reaction Time", "reaction_time", "rt"])
    participant_col = _detect_column(df, ["Participant", "participant_id", "participant"])
    mood_col = _detect_column(df, ["Mood", "mood_rating", "mood"])

    # 2. Flag outliers on raw reaction time (IQR per condition)
    df = _flag_outliers_iqr(df, condition_col, rt_col, k=1.5)

    # 3. Z‑score normalize reaction time per condition (overwrite column)
    df = _zscore_normalize(df, condition_col, rt_col)

    # 4. Save the preprocessed dataframe
    save_preprocessed_data(df, design_type, output_path)

    # 5. Generate outlier audit trail (uses a temporary column name expected by the legacy helper)
    try:
        df_audit = df.copy()
        df_audit['Normalized RT'] = df[rt_col]  # normalized values
        log_outlier_removal(df_audit, group_col=condition_col,
                            rt_col='Normalized RT')
    except Exception as e:
        logger.warning(f"Outlier audit trail could not be generated: {e}")

    # 6. T009 – aggregate features and persist them
    try:
        features_df = _aggregate_features(df,
                                          participant_col=participant_col,
                                          condition_col=condition_col,
                                          rt_col=rt_col,
                                          mood_col=mood_col)
        features_path = os.path.join(get_path('processed'), 'features_ds000208.csv')
        _save_features(features_df, features_path)
    except Exception as e:
        logger.warning(f"Feature aggregation (T009) failed: {e}")

    logger.info("Preprocessing pipeline (T008 + T009) completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Preprocessing Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV or directory of raw CSVs")
    parser.add_argument("--output", required=True, help="Path to output CSV (used in file mode)")
    parser.add_argument("--design_type", default="Within-Subjects", help="Design type (Within-Subjects or Between-Subjects)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    run_preprocessing(args.input, args.output, args.design_type)
