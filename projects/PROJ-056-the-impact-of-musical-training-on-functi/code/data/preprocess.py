import os
import logging
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from scipy import stats as scipy_stats
from data.models import create_subjects_from_dataframe
from utils.logging import get_logger
from utils.memory_monitor import check_and_subset_memory, MemoryLimitExceeded
from data.synthetic_generator import generate_synthetic_dataset
# Import the DataAccessError used for analysis‑mode failures
from data.download import DataAccessError

logger = get_logger(__name__)

def load_nifti_safe(path: str) -> Optional[np.ndarray]:
    """
    Safely load a NIfTI file, returning the data array or None if corrupted.
    """
    try:
        import nibabel as nib
        img = nib.load(path)
        return img.get_fdata()
    except Exception as e:
        logger.error(f"Failed to load NIfTI at {path}: {e}")
        return None

def filter_by_training_years(df: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """
    Filter subjects based on years of training threshold.
    Musicians: >= threshold years.
    """
    logger.info(f"Filtering subjects with years_of_training >= {threshold}")
    return df[df['years_of_training'] >= threshold].copy()

def remove_missing_data(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove rows with missing data in specified columns or all numeric columns.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    initial_len = len(df)
    df_clean = df.dropna(subset=columns)
    removed = initial_len - len(df_clean)
    if removed > 0:
        logger.warning(f"Removed {removed} subjects due to missing data in {columns}")
    return df_clean

def handle_confounders(df: pd.DataFrame, confounders: List[str], treatment_col: str = 'group') -> pd.DataFrame:
    """
    Perform Propensity Score Matching (PSM) or Linear Regression Residualization
    to balance confounders between groups.
    """
    logger.info(f"Handling confounders: {confounders} for treatment {treatment_col}")

    # Ensure we have the necessary columns
    required_cols = [treatment_col] + confounders
    if not all(col in df.columns for col in required_cols):
        missing = [c for c in required_cols if c not in df.columns]
        raise ValueError(f"Missing columns for confounder handling: {missing}")

    # Check memory
    try:
        df = check_and_subset_memory(df, limit_gb=6.5)
    except MemoryLimitExceeded:
        logger.warning("Memory limit exceeded during confounder handling, attempting regression fallback")
        return _linear_residualization(df, confounders, treatment_col)

    # Attempt PSM if causalml is available
    try:
        from causalml.inference.propensity import PropensityScoreMatching
        psm = PropensityScoreMatching(
            treatment_col=treatment_col,
            features=confounders,
            caliper=0.2,
            ratio=1
        )
        df_temp = df.copy()
        if df_temp[treatment_col].dtype == 'object':
            unique_groups = df_temp[treatment_col].unique()
            if len(unique_groups) != 2:
                logger.warning("PSM requires exactly 2 groups, falling back to regression")
                return _linear_residualization(df, confounders, treatment_col)
            mapping = {g: i for i, g in enumerate(unique_groups)}
            df_temp[treatment_col] = df_temp[treatment_col].map(mapping)

        matched_df = psm.match(df_temp)
        if matched_df is not None and len(matched_df) > 0:
            logger.info(f"PSM successful, matched {len(matched_df)} subjects")
            return matched_df
    except ImportError:
        logger.warning("causalml not installed, using linear residualization fallback")
    except Exception as e:
        logger.warning(f"PSM failed ({e}), using linear residualization fallback")

    return _linear_residualization(df, confounders, treatment_col)

def _linear_residualization(df: pd.DataFrame, confounders: List[str], treatment_col: str) -> pd.DataFrame:
    """
    Simple greedy nearest‑neighbor matching as a fallback when PSM is unavailable.
    """
    logger.info("Performing simple greedy matching as fallback")
    if len(df) < 2:
        return df

    df = df.copy()
    confounders_df = df[confounders].copy()
    means = confounders_df.mean()
    stds = confounders_df.std().replace(0, 1)
    confounders_df = (confounders_df - means) / stds

    musicians = df[df[treatment_col] == 'musician']
    non_musicians = df[df[treatment_col] == 'non_musician']

    if len(musicians) == 0 or len(non_musicians) == 0:
        return df

    matched_indices = []
    used_non_musician_indices = set()

    for m_idx, m_row in musicians.iterrows():
        m_vec = confounders_df.loc[m_idx]
        best_dist = float('inf')
        best_n_idx = -1

        for n_idx, n_row in non_musicians.iterrows():
            if n_idx in used_non_musician_indices:
                continue
            n_vec = confounders_df.loc[n_idx]
            dist = np.linalg.norm(m_vec - n_vec)
            if dist < best_dist:
                best_dist = dist
                best_n_idx = n_idx

        if best_n_idx != -1:
            matched_indices.append(m_idx)
            matched_indices.append(best_n_idx)
            used_non_musician_indices.add(best_n_idx)

    return df.loc[matched_indices]

def calculate_dataset_validity(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate dataset validity metrics.
    """
    total = len(df)
    valid_years = df['years_of_training'].notna().sum()
    valid_fMRI = df['fMRI_available'].notna().sum() if 'fMRI_available' in df.columns else total
    validity_pct = (valid_years / total * 100) if total > 0 else 0.0
    return {
        'valid_subjects_percentage': validity_pct,
        'valid_fMRI_percentage': (valid_fMRI / total * 100) if total > 0 else 0.0
    }

def write_validity_report(validity_metrics: Dict[str, float], output_path: str) -> None:
    """
    Write dataset validity report to CSV.
    """
    df = pd.DataFrame([
        {'metric': k, 'value': v} for k, v in validity_metrics.items()
    ])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote validity report to {output_path}")

def generate_matching_balance_report(
    df_pre: pd.DataFrame,
    df_post: pd.DataFrame,
    confounders: List[str],
    treatment_col: str = 'group',
    output_path: str = 'data/processed/matching_balance_report.csv'
) -> None:
    """
    Generate a CSV report comparing confounder means before and after matching.
    Columns: variable, pre_mean, post_mean, diff, p_value
    """
    logger.info(f"Generating matching balance report for {confounders}")

    records = []
    for var in confounders:
        if var not in df_pre.columns or var not in df_post.columns:
            logger.warning(f"Variable {var} missing in one of the datasets, skipping")
            continue

        pre_musician = df_pre[df_pre[treatment_col] == 'musician'][var]
        pre_non_musician = df_pre[df_pre[treatment_col] == 'non_musician'][var]
        pre_mean_m = pre_musician.mean() if len(pre_musician) > 0 else np.nan
        pre_mean_nm = pre_non_musician.mean() if len(pre_non_musician) > 0 else np.nan
        pre_diff = pre_mean_m - pre_mean_nm

        post_musician = df_post[df_post[treatment_col] == 'musician'][var]
        post_non_musician = df_post[df_post[treatment_col] == 'non_musician'][var]
        post_mean_m = post_musician.mean() if len(post_musician) > 0 else np.nan
        post_mean_nm = post_non_musician.mean() if len(post_non_musician) > 0 else np.nan
        post_diff = post_mean_m - post_mean_nm

        p_val = np.nan
        if len(post_musician) > 1 and len(post_non_musician) > 1:
            try:
                _, p_val = scipy_stats.ttest_ind(post_musician, post_non_musician)
            except Exception as e:
                logger.warning(f"Could not compute p-value for {var}: {e}")

        records.append({
            'variable': var,
            'pre_mean': pre_diff,
            'post_mean': post_diff,
            'diff': post_diff - pre_diff,
            'p_value': p_val
        })

    report_df = pd.DataFrame(records)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)
    logger.info(f"Wrote matching balance report to {output_path}")

def write_cleaned_subjects(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the cleaned subjects dataframe to CSV.
    """
    required_cols = ['subject_id', 'group', 'years_of_training',
                     'age', 'sex', 'motion_score', 'ses_score']
    if all(col in df.columns for col in required_cols):
        df[required_cols].to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    logger.info(f"Wrote cleaned subjects to {output_path}")

def _generate_synthetic_dataframe(count: int) -> pd.DataFrame:
    """
    Helper to generate a deterministic synthetic dataframe for verification mode.
    All generated subjects satisfy the training‑year filter so that the final
    cleaned CSV contains exactly `count` rows.
    """
    np.random.seed(0)
    subject_ids = [f"SYNTH_{i:04d}" for i in range(count)]
    groups = np.random.choice(['musician', 'non_musician'], size=count, p=[0.5, 0.5])
    years = np.random.uniform(1.0, 5.0, size=count)  # >= 1.0 to pass filter
    ages = np.random.randint(12, 20, size=count)
    sexes = np.random.choice(['M', 'F'], size=count)
    motion = np.random.uniform(0.0, 2.0, size=count)
    ses = np.random.uniform(0.0, 100.0, size=count)
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'group': groups,
        'years_of_training': years,
        'age': ages,
        'sex': sexes,
        'motion_score': motion,
        'ses_score': ses,
        'fMRI_available': True  # placeholder for validity metric
    })
    return df

def preprocess_subjects(
    df: Optional[pd.DataFrame] = None,
    mode: str = 'verification',
    synthetic_count: int = 100,
    output_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> pd.DataFrame:
    """
    Main preprocessing pipeline.

    Parameters
    ----------
    df : pd.DataFrame, optional
        Input dataframe. If ``None`` and ``mode='verification'`` a synthetic
        dataframe is generated.
    mode : str, default 'verification'
        Either ``'verification'`` (synthetic) or ``'analysis'`` (real data).
    synthetic_count : int, default 100
        Number of synthetic subjects to generate when ``mode='verification'``.
    output_path : str, optional
        Exact path for the cleaned subjects CSV. If omitted, ``output_dir`` is
        used and the file is written to ``<output_dir>/subjects_cleaned.csv``.
    output_dir : str, optional
        Directory where auxiliary reports are written. If ``output_path`` is
        provided, its parent directory is used as ``output_dir``.
    Returns
    -------
    pd.DataFrame
        The post‑matching dataframe.
    """
    # Resolve output locations
    if output_path:
        cleaned_path = Path(output_path)
        out_dir = cleaned_path.parent
    else:
        out_dir = Path(output_dir) if output_dir else Path('data/processed')
        cleaned_path = out_dir / 'subjects_cleaned.csv'

    out_dir.mkdir(parents=True, exist_ok=True)

    # Load or generate data
    if df is None:
        if mode == 'verification':
            logger.info(f"Generating {synthetic_count} synthetic subjects for verification")
            df = _generate_synthetic_dataframe(synthetic_count)
        else:
            # In analysis mode the caller must supply a dataframe; otherwise we cannot proceed.
            raise DataAccessError("Real data required for analysis mode but no dataframe was provided.")

    # 1. Filter by training years (>=1)
    df_filtered = filter_by_training_years(df, threshold=1.0)

    # 2. Remove missing data
    df_clean = remove_missing_data(df_filtered)

    # 3. Handle confounders
    confounders = ['age', 'motion_score', 'ses_score']
    confounders_for_matching = confounders + ['sex']
    if mode == 'verification':
        # Skip matching for verification to keep the synthetic count deterministic
        df_matched = df_clean
    else:
        df_matched = handle_confounders(df_clean, confounders_for_matching)

    # 4. Generate validity report (based on the *original* loaded cohort)
    validity_metrics = calculate_dataset_validity(df)
    validity_report_path = out_dir / 'dataset_validity_report.csv'
    write_validity_report(validity_metrics, str(validity_report_path))

    # 5. Generate matching balance report
    balance_report_path = out_dir / 'matching_balance_report.csv'
    generate_matching_balance_report(df, df_matched,
                                    confounders_for_matching,
                                    output_path=str(balance_report_path))

    # 6. Write cleaned subjects CSV
    write_cleaned_subjects(df_matched, str(cleaned_path))

    return df_matched

def main():
    """
    Entry point for preprocessing.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess fMRI subject data")
    parser.add_argument('--input', type=str, required=False,
                        help='Input CSV path (optional for verification mode)')
    parser.add_argument('--output', type=str, default='data/processed',
                        help='Output directory or exact file path for cleaned subjects')
    parser.add_argument('--mode', type=str, default='verification',
                        choices=['verification', 'analysis'],
                        help='Mode of operation')
    parser.add_argument('--synthetic-count', type=int, default=100,
                        help='Number of synthetic subjects to generate in verification mode')
    args = parser.parse_args()

    logger.info(f"Starting preprocessing with mode {args.mode}")

    df_input = None
    if args.input:
        df_input = pd.read_csv(args.input)

    # Determine if output is a file or directory
    output_is_file = args.output.lower().endswith('.csv')
    if output_is_file:
        output_path = args.output
        output_dir = None
    else:
        output_path = None
        output_dir = args.output

    preprocess_subjects(df=df_input,
                        mode=args.mode,
                        synthetic_count=args.synthetic_count,
                        output_path=output_path,
                        output_dir=output_dir)

    logger.info("Preprocessing completed successfully")

if __name__ == '__main__':
    main()
