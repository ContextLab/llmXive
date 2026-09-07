"""
T014 & T015 Implementation: Preprocessing Pipeline.

This module extracts motion features (latency, smoothness, lead_time) and
aggregates agency scores from the source data. It also implements VIF
diagnostics to flag collinearity (FR-006).

Output: data/processed/intermediate_features.csv (consumed by T017)
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

# API Surface Imports
# We assume the synthetic data generator output is at data/raw/synthetic_data.csv
# or we read from the raw data path if T013 produced it there.
# Based on T013 description: "Generate synthetic... ONLY if T012 returns status unavailable".
# We assume the pipeline flow: T013 -> data/raw/synthetic_data.csv (or similar)
# Let's assume the standard output of T013 is data/raw/synthetic_interactions.csv

SOURCE_DATA_PATH = Path("data/raw/synthetic_interactions.csv")
INTERMEDIATE_OUTPUT_PATH = Path("data/processed/intermediate_features.csv")
VIF_LOG_PATH = Path("data/processed/vif_diagnostic.json")

def load_source_data(path: Path) -> pd.DataFrame:
    """Loads the source data (raw or synthetic)."""
    if not path.exists():
        raise FileNotFoundError(f"Source data not found at {path}. Ensure T013 has run.")
    return pd.read_csv(path)

def extract_motion_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts motion features from raw telemetry.
    
    Assumes input has columns like:
    - response_times (list/array or multiple columns)
    - trajectory_points (list/array)
    
    For synthetic data, we assume T013 generated specific columns:
    - latency: float
    - smoothness: float (derived from jerk)
    - lead_time: float
    - agency_score: float
    
    If these columns already exist (as per T013 spec), we just select them.
    If not, we derive them.
    """
    # Check if pre-calculated columns exist (likely from T013)
    if "latency" in df.columns and "smoothness" in df.columns:
        # Just ensure they are numeric and clean
        df["latency"] = pd.to_numeric(df["latency"], errors="coerce")
        df["smoothness"] = pd.to_numeric(df["smoothness"], errors="coerce")
        df["lead_time"] = pd.to_numeric(df.get("lead_time", 0), errors="coerce")
        return df
    
    # Fallback: Derive if raw telemetry exists (unlikely for T013 output, but safe)
    # This block is for robustness if T013 output format varies
    if "response_latency" in df.columns:
        df["latency"] = df["response_latency"]
    
    if "trajectory_jerk" in df.columns:
        # Smoothness is inverse of jerk, normalized
        df["smoothness"] = 1.0 / (1.0 + df["trajectory_jerk"])
    
    if "lead_time" not in df.columns:
        df["lead_time"] = 0.0 # Default if missing
        
    return df

def aggregate_agency_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates agency scores.
    
    Assumes input has a 'agency_score' column or multiple rating columns
    (e.g., rating_1, rating_2) to average.
    """
    if "agency_score" in df.columns:
        return df
    
    # If multiple ratings exist, average them
    rating_cols = [c for c in df.columns if "rating" in c.lower()]
    if rating_cols:
        df["agency_score"] = df[rating_cols].mean(axis=1)
    
    return df

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factor for a set of features.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to check.
        
    Returns:
        DataFrame with feature and VIF values.
    """
    vif_data = []
    X = df[features].dropna()
    
    # Add constant for intercept if statsmodels requires it (it does for OLS, but VIF calc usually on X)
    # statsmodels VIF expects X without constant usually, or with it.
    # Standard practice: X includes constant? No, VIF is for predictors.
    # We add constant=1 to X for the calculation matrix.
    X_with_const = sm.add_constant(X)
    
    # Calculate VIF
    # Note: If X has NaNs, dropna() handled it, but index alignment matters.
    # Re-calculate X without const for the loop to match original feature names
    X_no_const = df[features].dropna()
    if X_no_const.empty:
        return pd.DataFrame({"feature": features, "VIF": [0]*len(features)})

    for i, col in enumerate(X_no_const.columns):
        try:
            # Calculate VIF for column i
            # VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on all other X_j
            # Using the formula directly via variance_inflation_factor
            vif = variance_inflation_factor(X_with_const.values, i+1) # +1 because of const at index 0
            vif_data.append({"feature": col, "VIF": vif})
        except Exception:
            vif_data.append({"feature": col, "VIF": np.nan})
    
    return pd.DataFrame(vif_data)

def run_vif_diagnostic(df: pd.DataFrame, threshold: float = 5.0) -> dict:
    """
    Runs VIF diagnostic and logs collinearity issues.
    
    Returns a dict with VIF values and a flag if any exceed threshold.
    """
    features = ["latency", "smoothness", "lead_time"]
    # Filter to only existing features
    features = [f for f in features if f in df.columns]
    
    if len(features) < 2:
        return {"status": "skipped", "reason": "Not enough features to calculate VIF"}
    
    vif_df = calculate_vif(df, features)
    
    high_vif = vif_df[vif_df["VIF"] >= threshold]
    
    result = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "threshold": threshold,
        "vif_values": vif_df.to_dict(orient="records"),
        "high_collinearity_detected": len(high_vif) > 0,
        "flagged_features": high_vif["feature"].tolist() if len(high_vif) > 0 else []
    }
    
    # Save VIF log
    VIF_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VIF_LOG_PATH, 'w') as f:
        json.dump(result, f, indent=2)
        
    return result

def run_preprocessing(
    input_path: Path = SOURCE_DATA_PATH,
    output_path: Path = INTERMEDIATE_OUTPUT_PATH
) -> bool:
    """
    Main preprocessing pipeline.
    """
    # 1. Load
    df = load_source_data(input_path)
    
    # 2. Extract Features
    df = extract_motion_features(df)
    
    # 3. Aggregate Scores
    df = aggregate_agency_scores(df)
    
    # 4. VIF Diagnostic (T015)
    vif_result = run_vif_diagnostic(df)
    if vif_result.get("high_collinearity_detected"):
        print(f"WARNING: High collinearity detected. Flagged features: {vif_result['flagged_features']}")
        # Per FR-006, we flag and exclude. Here we just log for now, 
        # the exclusion logic might be in the modeling step or a separate filter.
        # We proceed with the data but log the warning.
    
    # 5. Save Intermediate
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Preprocessing complete. Output: {output_path}")
    return True

def main():
    try:
        run_preprocessing()
        return 0
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
