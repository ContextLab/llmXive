"""
Control for proxy confounders in the model input matrix.

This module implements FR-008: Add logic to include proxy confounders
(lives saved/lost, species, age, gender) as control variables in the
model input matrix to isolate the salience effect.

The implementation operationalizes the Aristotelian/Socratic critique by
ensuring that the 'salience effect' is measured only after accounting for
objective outcome severity and agent characteristics, preventing the
conflation of 'spectacle' with 'moral virtue'.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

import pandas as pd
import numpy as np
from scipy import stats

# Project-relative imports based on provided API surface
# Note: We assume this file is run from the project root or code/ directory
# The import paths below assume the standard project structure
try:
    from data_models import Species, Gender
except ImportError:
    # Fallback for direct execution context if package structure isn't set
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_models import Species, Gender


logger = logging.getLogger(__name__)


def load_preprocessed_data(data_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load the preprocessed data containing salience scores and raw features.

    Args:
        data_path: Path to the processed CSV file.

    Returns:
        DataFrame with salience and raw data.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {path}")

    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def encode_categorical(df: pd.DataFrame, column: str, mapping: Optional[Dict] = None) -> pd.Series:
    """
    Encode a categorical column into numeric values.

    If a mapping is provided, use it. Otherwise, use pandas get_dummies or ordinal encoding.
    For this task, we use a simple ordinal encoding strategy for known enums.
    """
    if mapping:
        return df[column].map(mapping).fillna(-1).astype(int)

    # Default: simple label encoding
    unique_vals = df[column].dropna().unique()
    sort_vals = sorted([str(v) for v in unique_vals])
    label_map = {val: i for i, val in enumerate(sort_vals)}
    return df[column].map(label_map).fillna(-1).astype(int)


def extract_control_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and prepare proxy control variables as per FR-008.

    This function operationalizes the 'Outcome Severity' and 'Agent Type'
    proxies discussed in the Aristotelian review (T038, T039).

    Controls included:
    1. Outcome Severity: Derived from 'lives_lost' (continuous) and 'lives_saved' (continuous).
    2. Agent Characteristics:
       - Species (categorical -> numeric)
       - Age (categorical -> numeric)
       - Gender (categorical -> numeric)
       - Social Status (categorical -> numeric) - Optional, if available

    Returns:
        DataFrame containing ONLY the control variables, ready for regression.
    """
    controls = {}

    # 1. Outcome Severity (Material Cause proxy)
    # FR-008 specifies 'lives_lost' and 'lives_saved'
    if 'lives_lost' in df.columns:
        controls['outcome_severity_lost'] = pd.to_numeric(df['lives_lost'], errors='coerce').fillna(0)
    else:
        logger.warning("Column 'lives_lost' not found. Skipping outcome severity.")

    if 'lives_saved' in df.columns:
        controls['outcome_severity_saved'] = pd.to_numeric(df['lives_saved'], errors='coerce').fillna(0)
    else:
        logger.warning("Column 'lives_saved' not found. Skipping outcome severity saved.")

    # 2. Agent Characteristics (Formal Cause proxies)
    # Species
    if 'species' in df.columns:
        # Map Species enum to numeric if possible, otherwise string map
        species_map = {s.value: i for i, s in enumerate(Species)}
        controls['species_code'] = encode_categorical(df, 'species', species_map)
    else:
        logger.warning("Column 'species' not found.")

    # Age
    if 'age' in df.columns:
        age_map = {'child': 0, 'young': 1, 'adult': 2, 'elderly': 3}
        # Handle potential string variations
        controls['age_code'] = encode_categorical(df, 'age', age_map)
    else:
        logger.warning("Column 'age' not found.")

    # Gender
    if 'gender' in df.columns:
        gender_map = {g.value: i for i, g in enumerate(Gender)}
        controls['gender_code'] = encode_categorical(df, 'gender', gender_map)
    else:
        logger.warning("Column 'gender' not found.")

    # Social Status (Optional but recommended for robust control)
    if 'social_status' in df.columns:
        status_map = {'homeless': 0, 'criminal': 1, 'pregnant': 2, 'executive': 3, 'athlete': 4, 'doctor': 5, 'lawyer': 6, 'judge': 7}
        controls['status_code'] = encode_categorical(df, 'social_status', status_map)
    else:
        logger.debug("Column 'social_status' not found. Continuing without it.")

    # Convert to DataFrame
    controls_df = pd.DataFrame(controls)
    logger.info(f"Extracted {len(controls_df.columns)} control variables.")
    return controls_df


def prepare_model_matrix_with_controls(
    df: pd.DataFrame,
    target_col: str = 'choice',
    salience_col: str = 'salience_score'
) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
    """
    Prepare the full model input matrix including salience and control variables.

    This ensures that when we fit the aDDM or regression model, the salience
    coefficient is conditioned on the proxy confounders.

    Args:
        df: Full dataset with salience and raw columns.
        target_col: Name of the target variable (choice).
        salience_col: Name of the salience score column.

    Returns:
        Tuple of (X_matrix, y_vector)
        X_matrix includes: [salience_score, outcome_severity_lost, outcome_severity_saved, species_code, age_code, gender_code, status_code]
    """
    # Extract controls
    controls = extract_control_variables(df)

    # Extract salience
    salience = pd.to_numeric(df[salience_col], errors='coerce').fillna(0)

    # Construct X matrix
    X_dict = {
        'salience': salience
    }
    X_dict.update(controls)

    X = pd.DataFrame(X_dict)

    # Extract Y
    y = pd.to_numeric(df[target_col], errors='coerce')

    # Drop rows with any NaN in controls or target
    valid_idx = X.index[y.notna() & X.notna().all(axis=1)]
    X = X.loc[valid_idx]
    y = y.loc[valid_idx]

    logger.info(f"Final model matrix shape: {X.shape} (after dropping {len(df) - len(X)} invalid rows)")

    return X, y


def isolate_salience_effect(
    df: pd.DataFrame,
    target_col: str = 'choice',
    salience_col: str = 'salience_score',
    method: str = 'residualize'
) -> Dict[str, Any]:
    """
    Isolate the salience effect by regressing out control variables.

    Method 'residualize':
    1. Regress Y (choice) on Controls -> get residuals (Y_resid)
    2. Regress X (salience) on Controls -> get residuals (X_resid)
    3. Correlate Y_resid and X_resid.
    This gives the partial correlation of Salience and Choice, controlling for confounders.

    Args:
        df: Dataset.
        target_col: Target variable name.
        salience_col: Salience variable name.
        method: Currently only 'residualize' is supported.

    Returns:
        Dictionary with correlation coefficient, p-value, and R-squared of the control model.
    """
    X, y = prepare_model_matrix_with_controls(df, target_col, salience_col)

    if len(X) < 10:
        raise ValueError("Insufficient data points after filtering.")

    controls = X.drop(columns=['salience'])
    salience = X['salience']

    # 1. Regress Y on Controls
    # y = beta_0 + beta_1*Controls + epsilon_y
    # We use a simple linear regression for this diagnostic
    from sklearn.linear_model import LinearRegression

    reg_y = LinearRegression()
    reg_y.fit(controls, y)
    y_resid = y - reg_y.predict(controls)

    # 2. Regress Salience on Controls
    # x = alpha_0 + alpha_1*Controls + epsilon_x
    reg_x = LinearRegression()
    reg_x.fit(controls, salience)
    x_resid = salience - reg_x.predict(controls)

    # 3. Correlation between residuals
    corr, p_value = stats.pearsonr(x_resid, y_resid)

    # R-squared of the control model for Y
    r2_y = reg_y.score(controls, y)

    return {
        'partial_correlation': float(corr),
        'p_value': float(p_value),
        'r_squared_controls': float(r2_y),
        'n_observations': len(X),
        'controls_used': list(controls.columns)
    }


def generate_control_report(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    target_col: str = 'choice',
    salience_col: str = 'salience_score'
) -> Dict[str, Any]:
    """
    Generate a report on the control variable impact and isolated salience effect.

    Args:
        df: Dataset.
        output_path: Path to write the JSON report.
        target_col: Target variable.
        salience_col: Salience variable.

    Returns:
        Report dictionary.
    """
    try:
        result = isolate_salience_effect(df, target_col, salience_col)
    except Exception as e:
        logger.error(f"Failed to isolate salience effect: {e}")
        result = {
            'error': str(e),
            'partial_correlation': None,
            'p_value': None
        }

    report = {
        'analysis': 'Control Variable Isolation (FR-008)',
        'description': 'Partial correlation of salience with choice, controlling for outcome severity and agent demographics.',
        'results': result
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Control report written to {path}")
    return report


def main():
    """
    Entry point for running the control confounder analysis.

    Usage:
        python code/analysis/control_confounders.py --input data/processed/salience_merged.csv --output data/reports/control_isolation.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Isolate salience effect by controlling for proxy confounders.")
    parser.add_argument('--input', type=str, required=True, help='Path to preprocessed CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON report')
    parser.add_argument('--target', type=str, default='choice', help='Target column name')
    parser.add_argument('--salience', type=str, default='salience_score', help='Salience column name')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        df = load_preprocessed_data(args.input)
        report = generate_control_report(df, args.output, args.target, args.salience)
        print(json.dumps(report, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()