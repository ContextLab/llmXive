import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from utils.logging import get_logger
from utils.config import get_project_paths

# Ensure logger is initialized
logger = get_logger(__name__)

# Constants for ATP-III criteria (Strict thresholds)
# BMI >= 30.0 kg/m^2 OR waist circumference > 102cm (men) / > 88cm (women)
# We assume waist circumference is not available in GTEx, so we use BMI >= 30.0
BMI_THRESHOLD = 30.0
GLUCOSE_THRESHOLD = 100  # mg/dL
BP_SYSTOLIC_THRESHOLD = 130  # mmHg
BP_DIASTOLIC_THRESHOLD = 85  # mmHg
TRIGLYCERIDES_THRESHOLD = 150  # mg/dL
HDL_MALE_THRESHOLD = 40  # mg/dL
HDL_FEMALE_THRESHOLD = 50  # mg/dL

def classify_metabolic_status(
    df: pd.DataFrame,
    bmi_col: str = "bmi",
    glucose_col: str = "glucose",
    systolic_bp_col: str = "systolic_bp",
    diastolic_bp_col: str = "diastolic_bp",
    tg_col: str = "triglycerides",
    hdl_col: str = "hdl",
    sex_col: str = "sex"
) -> pd.DataFrame:
    """
    Classify samples as Metabolic Syndrome (MetS) or Control based on ATP-III criteria.
    
    Criteria: Presence of 3 or more of the following 5 factors:
    1. Elevated Waist Circumference (Not available in GTEx, substituting BMI >= 30)
    2. Elevated Triglycerides (>= 150 mg/dL)
    3. Reduced HDL (< 40 mg/dL men, < 50 mg/dL women)
    4. Elevated Blood Pressure (>= 130/85 mmHg)
    5. Elevated Fasting Glucose (>= 100 mg/dL)

    Args:
        df: DataFrame containing clinical variables.
        bmi_col: Name of the BMI column.
        glucose_col: Name of the glucose column.
        systolic_bp_col: Name of the systolic blood pressure column.
        diastolic_bp_col: Name of the diastolic blood pressure column.
        tg_col: Name of the triglycerides column.
        hdl_col: Name of the HDL column.
        sex_col: Name of the sex column ('M' or 'F').

    Returns:
        DataFrame with an added 'metabolic_status' column ('MetS' or 'Control').
        Samples with missing critical data are excluded and logged.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return df.copy()

    result_df = df.copy()
    
    # Check for required columns
    required_cols = [bmi_col, glucose_col, systolic_bp_col, diastolic_bp_col, tg_col, hdl_col, sex_col]
    missing_cols = [c for c in required_cols if c not in result_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for ATP-III classification: {missing_cols}")

    # Initialize criteria flags
    criteria_count = 0

    # 1. BMI >= 30.0 (Proxy for Waist Circumference)
    # Handle missing values: if NaN, the criterion is not met (and contributes to missing data logic)
    bmi_flag = result_df[bmi_col].notna() & (result_df[bmi_col] >= BMI_THRESHOLD)
    criteria_count += bmi_flag.astype(int)

    # 2. Elevated Triglycerides
    tg_flag = result_df[tg_col].notna() & (result_df[tg_col] >= TRIGLYCERIDES_THRESHOLD)
    criteria_count += tg_flag.astype(int)

    # 3. Reduced HDL (Sex-specific)
    # Convert sex to string if necessary
    result_df[sex_col] = result_df[sex_col].astype(str).str.upper()
    hdl_flag = pd.Series(False, index=result_df.index)
    male_mask = result_df[sex_col] == 'M'
    female_mask = result_df[sex_col] == 'F'
    
    if male_mask.any():
        hdl_flag.loc[male_mask] = result_df.loc[male_mask, hdl_col].notna() & (result_df.loc[male_mask, hdl_col] < HDL_MALE_THRESHOLD)
    if female_mask.any():
        hdl_flag.loc[female_mask] = result_df.loc[female_mask, hdl_col].notna() & (result_df.loc[female_mask, hdl_col] < HDL_FEMALE_THRESHOLD)
    criteria_count += hdl_flag.astype(int)

    # 4. Elevated Blood Pressure (Systolic >= 130 OR Diastolic >= 85)
    # Both must be present to count as a valid measurement? Usually yes, but if one is high, it counts.
    # If either is NaN, we might not be able to confirm the condition, but standard ATP-III 
    # requires the measurement. If one is missing, we cannot confirm the BP criterion.
    # Strict interpretation: Both must be non-null to evaluate? 
    # Let's assume if either is high AND the other is not low (or missing), it counts? 
    # Standard practice: If either is high, it counts. If missing, we can't say it's high.
    # So: (SBP >= 130) OR (DBP >= 85), provided the value used is not NaN.
    bp_flag = pd.Series(False, index=result_df.index)
    sbp_high = result_df[systolic_bp_col].notna() & (result_df[systolic_bp_col] >= BP_SYSTOLIC_THRESHOLD)
    dbp_high = result_df[diastolic_bp_col].notna() & (result_df[diastolic_bp_col] >= BP_DIASTOLIC_THRESHOLD)
    bp_flag = sbp_high | dbp_high
    criteria_count += bp_flag.astype(int)

    # 5. Elevated Fasting Glucose
    glucose_flag = result_df[glucose_col].notna() & (result_df[glucose_col] >= GLUCOSE_THRESHOLD)
    criteria_count += glucose_flag.astype(int)

    # Determine MetS status
    # MetS if >= 3 criteria are met
    result_df['metabolic_status'] = criteria_count.apply(lambda x: 'MetS' if x >= 3 else 'Control')

    # Log exclusion of samples with missing data in critical variables
    # We need to identify rows where ANY of the 5 clinical variables are missing.
    # If a variable is missing, we cannot definitively calculate the criteria count.
    # However, the prompt says "exclude samples with null/NaN/invalid values".
    # Let's filter the dataframe to only include rows where ALL 5 variables are present.
    clinical_cols = [bmi_col, glucose_col, systolic_bp_col, diastolic_bp_col, tg_col, hdl_col]
    mask_complete = result_df[clinical_cols].notna().all(axis=1)
    
    total_before = len(result_df)
    result_df = result_df[mask_complete].copy()
    excluded_count = total_before - len(result_df)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} samples due to missing clinical data (BMI, Glucose, BP, TG, or HDL).")
    else:
        logger.info("All samples have complete clinical data.")

    return result_df

def calculate_effect_size_from_data(
    df: pd.DataFrame,
    gene_col: str,
    group_col: str = "metabolic_status"
) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size between two groups for a given gene.
    
    Args:
        df: DataFrame with gene expression and group labels.
        gene_col: Name of the gene expression column.
        group_col: Name of the group column (e.g., 'MetS' vs 'Control').
    
    Returns:
        Dictionary with 'cohen_d' and 'n_metS', 'n_control'.
    """
    if df.empty or group_col not in df.columns or gene_col not in df.columns:
        return {"cohen_d": 0.0, "n_metS": 0, "n_control": 0}

    metS_group = df[df[group_col] == 'MetS'][gene_col].dropna()
    control_group = df[df[group_col] == 'Control'][gene_col].dropna()

    n_metS = len(metS_group)
    n_control = len(control_group)

    if n_metS == 0 or n_control == 0:
        return {"cohen_d": 0.0, "n_metS": n_metS, "n_control": n_control}

    mean_metS = metS_group.mean()
    mean_control = control_group.mean()
    std_metS = metS_group.std()
    std_control = control_group.std()

    # Pooled standard deviation
    pooled_std = np.sqrt(((n_metS - 1) * std_metS**2 + (n_control - 1) * std_control**2) / (n_metS + n_control - 2))

    if pooled_std == 0:
        cohen_d = 0.0
    else:
        cohen_d = (mean_metS - mean_control) / pooled_std

    return {
        "cohen_d": float(cohen_d),
        "n_metS": n_metS,
        "n_control": n_control
    }

def run_power_analysis(
    n_samples: int,
    alpha: float = 0.05,
    power_target: float = 0.80,
    effect_size: float = 0.5
) -> Dict[str, Any]:
    """
    Perform a simple power analysis to determine if the sample size is sufficient.
    This is a placeholder for a more complex calculation using statsmodels.
    For this implementation, we assume a two-sample t-test scenario.
    
    Args:
        n_samples: Total number of complete cases.
        alpha: Significance level.
        power_target: Target statistical power.
        effect_size: Expected effect size (Cohen's d).
    
    Returns:
        Dictionary with 'status', 'power', 'n', 'message'.
    """
    try:
        from statsmodels.stats.power import TTestIndPower
    except ImportError:
        logger.error("statsmodels is required for power analysis. Please install it.")
        return {"status": "Error", "power": 0.0, "n": n_samples, "message": "statsmodels not installed"}

    analysis = TTestIndPower()
    
    # Assume equal group sizes for estimation
    n_per_group = n_samples / 2
    
    if n_per_group < 10:
        return {
            "status": "Infeasible",
            "power": 0.0,
            "n": n_samples,
            "message": "Sample size too small for reliable power analysis."
        }

    try:
        calculated_power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=n_per_group,
            alpha=alpha,
            ratio=1.0,
            alternative='two-sided'
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}. Assuming low power.")
        calculated_power = 0.0

    status = "Feasible" if calculated_power >= power_target else "Infeasible"
    
    result = {
        "status": status,
        "power": float(calculated_power),
        "n": n_samples,
        "message": f"Power analysis complete. Power: {calculated_power:.2f}"
    }

    if status == "Infeasible":
        logger.critical(f"Statistical power ({calculated_power:.2f}) is below target ({power_target}). Pipeline halted.")
        # Write feasibility report and exit
        paths = get_project_paths()
        report_path = paths["processed"] / "feasibility_report.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)
    
    return result

def store_baseline_labels(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Store the baseline metabolic syndrome classifications to a CSV file.
    
    This function takes a DataFrame that has already been classified (contains 'metabolic_status')
    and writes the sample IDs and their labels to `data/processed/baseline_labels.csv`.
    
    Args:
        df: DataFrame containing 'sample_id' (or similar index) and 'metabolic_status'.
        output_path: Optional path to write the CSV. If None, uses default project path.
    
    Returns:
        Path to the written CSV file.
    """
    if df.empty:
        logger.warning("No data to store. Skipping baseline labels output.")
        return Path()

    if 'metabolic_status' not in df.columns:
        raise ValueError("DataFrame must contain 'metabolic_status' column to store baseline labels.")

    if output_path is None:
        paths = get_project_paths()
        output_path = paths["processed"] / "baseline_labels.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Select relevant columns
    # Assuming 'sample_id' is the index or a column. If it's the index, reset it.
    if 'sample_id' not in df.columns:
        if isinstance(df.index, pd.Index) and df.index.name == 'sample_id':
            df = df.reset_index()
        elif isinstance(df.index, pd.RangeIndex):
            # If no explicit ID, we might need to generate one or use index
            # But usually GTEx has sample IDs. Let's assume 'sample_id' exists or is index.
            # If not, we use the index as ID.
            df = df.reset_index()
            if df.columns[0] == 'index':
                df.rename(columns={'index': 'sample_id'}, inplace=True)
    
    # Ensure sample_id is present
    if 'sample_id' not in df.columns:
        # Fallback: use index if no column named sample_id
        df['sample_id'] = df.index
    
    # Select columns
    cols_to_save = ['sample_id', 'metabolic_status']
    # Add other clinical variables if useful for verification? 
    # Task says "baseline classifications", so just ID and label is sufficient.
    # But let's include the 5 clinical variables for traceability.
    clinical_vars = ['bmi', 'glucose', 'systolic_bp', 'diastolic_bp', 'triglycerides', 'hdl', 'sex']
    existing_clinical = [c for c in clinical_vars if c in df.columns]
    cols_to_save.extend(existing_clinical)

    output_df = df[cols_to_save].copy()
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Baseline labels stored to {output_path}")
    
    return output_path
