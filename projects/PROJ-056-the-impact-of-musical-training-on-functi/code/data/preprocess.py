import os
import logging
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
from scipy import stats as scipy_stats
from data.models import create_subjects_from_dataframe
from utils.logging import get_logger
from utils.memory_monitor import check_and_subset_memory, MemoryLimitExceeded
from data.synthetic_generator import generate_synthetic_dataset
# Import the DataAccessError used for analysis‑mode failures
from data.download import DataAccessError

log = get_logger(__name__)

###########################################################################
# Helper utilities
###########################################################################

def load_nifti_safe(path: str) -> Optional[np.ndarray]:
    """
    Safely load a NIfTI file, returning the data array or None if corrupted.
    """
    try:
        import nibabel as nib
        img = nib.load(path)
        return img.get_fdata()
    except Exception as e:
        log.error(f"Failed to load NIfTI at {path}: {e}")
        return None

def filter_by_training_years(df: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """
    Keep only subjects with ``years_of_training`` >= ``threshold``.
    """
    log.info(f"Applying musician cutoff of {threshold} year(s)")
    return df[df["years_of_training"] >= threshold].copy()

def remove_missing_data(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Drop rows that have missing values in the supplied ``columns``.
    If ``columns`` is ``None`` all numeric columns are considered.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    initial_len = len(df)
    df_clean = df.dropna(subset=columns)
    removed = initial_len - len(df_clean)
    if removed > 0:
        log.warning(f"Removed {removed} subjects due to missing data in {columns}")
    return df_clean

###########################################################################
# Matching / residualisation utilities
###########################################################################

def _standardized_mean_difference(
    treated: pd.Series, control: pd.Series
) -> float:
    """
    Compute the absolute standardized mean difference (SMD) between two groups.
    """
    mean_t = treated.mean()
    mean_c = control.mean()
    var_t = treated.var()
    var_c = control.var()
    pooled_sd = np.sqrt((var_t + var_c) / 2.0)
    if pooled_sd == 0:
        return 0.0
    return abs(mean_t - mean_c) / pooled_sd

def compute_smds(
    df: pd.DataFrame,
    treatment_col: str,
    covariates: List[str],
) -> Dict[str, float]:
    """
    Compute SMD for each covariate in ``covariates`` between the two
    treatment groups defined by ``treatment_col``.
    """
    smd_dict = {}
    for cov in covariates:
        treated = df[df[treatment_col] == "musician"][cov]
        control = df[df[treatment_col] == "non_musician"][cov]
        smd = _standardized_mean_difference(treated, control)
        smd_dict[cov] = smd
    return smd_dict

def handle_confounders(
    df: pd.DataFrame,
    confounders: List[str],
    treatment_col: str = "group",
) -> pd.DataFrame:
    """
    Perform Propensity‑Score Matching (PSM) with a caliper of 0.2 SD.
    If the ``causalml`` package is unavailable, fall back to a simple
    greedy nearest‑neighbor matching based on Euclidean distance in the
    standardized covariate space.
    """
    log.info(f"Attempting confounder handling (matching) on {confounders}")

    # Verify required columns exist
    required = [treatment_col] + confounders
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for matching: {missing}")

    # Try PSM if causalml is present
    try:
        from causalml.inference.propensity import PropensityScoreMatching

        # Encode treatment as binary
        df_tmp = df.copy()
        mapping = {"musician": 1, "non_musician": 0}
        df_tmp[treatment_col] = df_tmp[treatment_col].map(mapping)

        psm = PropensityScoreMatching(
            treatment_col=treatment_col,
            features=confounders,
            caliper=0.2,
            ratio=1,
        )
        matched = psm.match(df_tmp)
        if matched is not None and not matched.empty:
            # Restore original group labels
            inv_map = {v: k for k, v in mapping.items()}
            matched[treatment_col] = matched[treatment_col].map(inv_map)
            log.info(f"PSM succeeded – matched {len(matched)} subjects")
            return matched
    except ImportError:
        log.warning("causalml not installed – falling back to greedy matching")
    except Exception as e:
        log.warning(f"PSM failed ({e}) – falling back to greedy matching")

    # Greedy matching fallback
    return _greedy_matching(df, confounders, treatment_col)

def _greedy_matching(
    df: pd.DataFrame,
    confounders: List[str],
    treatment_col: str,
) -> pd.DataFrame:
    """
    Simple nearest‑neighbor matching without external dependencies.
    """
    log.info("Running greedy nearest‑neighbor matching")
    df = df.copy()
    # Standardise covariates
    cov_df = df[confounders].astype(float)
    means = cov_df.mean()
    stds = cov_df.std().replace(0, 1)
    cov_std = (cov_df - means) / stds

    musicians = df[df[treatment_col] == "musician"]
    non_musicians = df[df[treatment_col] == "non_musician"]

    if musicians.empty or non_musicians.empty:
        log.warning("One of the groups is empty – returning original dataframe")
        return df

    matched_indices = []
    used_non = set()

    for m_idx, m_row in musicians.iterrows():
        m_vec = cov_std.loc[m_idx].values
        best_dist = np.inf
        best_n_idx = None
        for n_idx, n_row in non_musicians.iterrows():
            if n_idx in used_non:
                continue
            n_vec = cov_std.loc[n_idx].values
            dist = np.linalg.norm(m_vec - n_vec)
            if dist < best_dist:
                best_dist = dist
                best_n_idx = n_idx
        if best_n_idx is not None:
            matched_indices.extend([m_idx, best_n_idx])
            used_non.add(best_n_idx)

    matched_df = df.loc[matched_indices]
    log.info(f"Greedy matching retained {len(matched_df)} subjects")
    return matched_df

###########################################################################
# Reporting utilities
###########################################################################

def write_exclusion_report(
    missing_years: int,
    corrupted_nifti: int,
    output_path: str,
) -> None:
    """
    Write a plain‑text report summarising exclusion counts.
    """
    report = (
        f"Exclusion Report\\n"
        f"=================\\n"
        f"Subjects removed due to missing years_of_training: {missing_years}\\n"
        f"Subjects removed due to corrupted NIfTI files: {corrupted_nifti}\\n"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
    log.info(f"Wrote exclusion report to {output_path}")

def write_matching_balance_report(
    pre_smd: Dict[str, float],
    post_smd: Dict[str, float],
    output_path: str,
) -> None:
    """
    Write a CSV containing SMD values before and after matching.
    Columns: covariate, pre_smd, post_smd, diff (post‑pre)
    """
    records = []
    for cov in pre_smd.keys():
        pre = pre_smd.get(cov, np.nan)
        post = post_smd.get(cov, np.nan)
        diff = post - pre
        records.append(
            {
                "covariate": cov,
                "pre_smd": pre,
                "post_smd": post,
                "diff": diff,
            }
        )
    df_report = pd.DataFrame(records)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_report.to_csv(output_path, index=False)
    log.info(f"Wrote matching balance (SMD) report to {output_path}")

def write_cleaned_subjects(
    df: pd.DataFrame,
    csv_path: str,
    parquet_path: str,
) -> None:
    """
    Persist the cleaned subject table in both CSV and Parquet formats.
    """
    required = [
        "subject_id",
        "group",
        "years_of_training",
        "age",
        "sex",
        "motion_score",
        "ses_score",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.warning(f"Missing expected columns {missing} – writing what is available")
    df_subset = df[required] if not missing else df
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    df_subset.to_csv(csv_path, index=False)
    Path(parquet_path).parent.mkdir(parents=True, exist_ok=True)
    df_subset.to_parquet(parquet_path, index=False)
    log.info(f"Wrote cleaned subjects to {csv_path} and {parquet_path}")

###########################################################################
# Core preprocessing pipeline
###########################################################################

def preprocess_subjects(
    df: Optional[pd.DataFrame] = None,
    mode: str = "verification",
    synthetic_count: int = 100,
    output_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    End‑to‑end preprocessing.

    Parameters
    ----------
    df : pd.DataFrame | None
        Input subject table. If ``None`` and ``mode='verification'`` a synthetic
        table is generated.
    mode : {'verification', 'analysis'}
        ``verification`` uses synthetic data; ``analysis`` expects real data.
    synthetic_count : int
        Number of synthetic subjects to generate for verification mode.
    output_dir : str | None
        Directory where all artefacts are written. If ``None`` defaults to
        ``data/processed``.

    Returns
    -------
    pd.DataFrame
        The matched & filtered dataframe (post‑processing).
    """
    # Resolve output locations
    out_dir = Path(output_dir) if output_dir else Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load or generate the raw subject table
    # ------------------------------------------------------------------
    if df is None:
        if mode == "verification":
            log.info(f"Generating {synthetic_count} synthetic subjects for verification")
            df = _generate_synthetic_dataframe(synthetic_count)
        else:
            raise DataAccessError(
                "Real data required for analysis mode but no dataframe was provided."
            )

    # ------------------------------------------------------------------
    # 1. Apply musician cutoff (≥1 year)
    # ------------------------------------------------------------------
    df = filter_by_training_years(df, threshold=1.0)

    # ------------------------------------------------------------------
    # 2. Exclude subjects with missing years_of_training
    # ------------------------------------------------------------------
    before_missing = len(df)
    df = remove_missing_data(df, columns=["years_of_training"])
    missing_years = before_missing - len(df)

    # ------------------------------------------------------------------
    # 3. Exclude subjects with corrupted NIfTI files
    # ------------------------------------------------------------------
    nifti_dir = Path("data/raw/mock_nifti")
    corrupted = 0
    valid_indices = []
    for idx, row in df.iterrows():
        nifti_path = nifti_dir / f"{row['subject_id']}.nii.gz"
        if not nifti_path.is_file() or load_nifti_safe(str(nifti_path)) is None:
            corrupted += 1
        else:
            valid_indices.append(idx)
    df = df.loc[valid_indices]

    # Write exclusion report
    exclusion_report_path = out_dir / "exclusion_report.txt"
    write_exclusion_report(
        missing_years=missing_years,
        corrupted_nifti=corrupted,
        output_path=str(exclusion_report_path),
    )

    # ------------------------------------------------------------------
    # 4. Matching on confounders
    # ------------------------------------------------------------------
    confounders = ["age", "sex", "motion_score", "ses_score"]
    pre_smd = compute_smds(df, treatment_col="group", covariates=confounders)

    df_matched = handle_confounders(df, confounders, treatment_col="group")
    post_smd = compute_smds(df_matched, treatment_col="group", covariates=confounders)

    # ------------------------------------------------------------------
    # 5. Write matching balance (SMD) report
    # ------------------------------------------------------------------
    balance_report_path = out_dir / "matching_balance_report.csv"
    write_matching_balance_report(pre_smd, post_smd, str(balance_report_path))

    # ------------------------------------------------------------------
    # 6. Verify minimum sample size per group
    # ------------------------------------------------------------------
    group_counts = df_matched["group"].value_counts()
    if any(group_counts < 50):
        log.error("Sample Size Insufficient – one of the groups has <50 subjects")
        raise RuntimeError("Sample Size Insufficient")

    # ------------------------------------------------------------------
    # 7. Persist cleaned subject table (CSV + Parquet)
    # ------------------------------------------------------------------
    cleaned_csv = out_dir / "subjects_cleaned.csv"
    cleaned_parquet = out_dir / "subjects_cleaned.parquet"
    write_cleaned_subjects(df_matched, str(cleaned_csv), str(cleaned_parquet))

    return df_matched

###########################################################################
# Synthetic dataframe generator (deterministic for verification)
###########################################################################

def _generate_synthetic_dataframe(count: int) -> pd.DataFrame:
    """
    Deterministic synthetic subject table for verification mode.
    All subjects satisfy the musician cutoff so the final cleaned CSV
    contains exactly ``count`` rows (subject to exclusion logic).
    """
    np.random.seed(0)
    subject_ids = [f"SYNTH_{i:04d}" for i in range(count)]
    groups = np.random.choice(["musician", "non_musician"], size=count, p=[0.5, 0.5])
    years = np.random.uniform(1.0, 5.0, size=count)  # >=1.0 to pass cutoff
    ages = np.random.randint(12, 20, size=count)
    sexes = np.random.choice(["M", "F"], size=count)
    motion = np.random.uniform(0.0, 2.0, size=count)
    ses = np.random.uniform(0.0, 100.0, size=count)
    df = pd.DataFrame(
        {
            "subject_id": subject_ids,
            "group": groups,
            "years_of_training": years,
            "age": ages,
            "sex": sexes,
            "motion_score": motion,
            "ses_score": ses,
            "fMRI_available": True,  # placeholder flag
        }
    )
    return df

###########################################################################
# CLI entry point
###########################################################################

def main() -> None:
    """
    Command‑line interface for preprocessing.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess fMRI subject data")
    parser.add_argument(
        "--input",
        type=str,
        required=False,
        help="Path to input CSV/Parquet (optional for verification mode)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory where all output artefacts will be written",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="verification",
        choices=["verification", "analysis"],
        help="Mode of operation",
    )
    parser.add_argument(
        "--synthetic-count",
        type=int,
        default=100,
        help="Number of synthetic subjects to generate in verification mode",
    )
    args = parser.parse_args()

    df_input = None
    if args.input:
        if args.input.endswith(".parquet"):
            df_input = pd.read_parquet(args.input)
        else:
            df_input = pd.read_csv(args.input)

    try:
        preprocess_subjects(
            df=df_input,
            mode=args.mode,
            synthetic_count=args.synthetic_count,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        log.error(f"Preprocessing failed: {exc}")
        raise

    log.info("Preprocessing completed successfully")

if __name__ == "__main__":
    main()
