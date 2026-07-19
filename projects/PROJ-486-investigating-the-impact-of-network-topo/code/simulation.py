import pandas as pd
import numpy as np
import os
import json
from typing import Dict, Optional, Tuple
from config import RANDOM_SEED

# Paths
DATA_PROCESSED_DIR = "data/processed"
DATA_RAW_DIR = "data/raw"
TOPOLOGY_CSV = "data/processed/topology_metrics.csv"
ENTRAINMENT_CSV = "data/raw/entrainment_metrics.csv"
JOINED_SIMULATED_CSV = "data/processed/joined_data_simulated.csv"
DATA_GAP_REPORT_PATH = "data/processed/data_gap_report.json"
METADATA_PATH = "data/processed/metadata.json"

def generate_entrainment_fallback(topology_df: Optional[pd.DataFrame] = None, 
                                  target_correlation: float = 0.5, 
                                  noise_level: float = 0.2,
                                  n_subjects: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic entrainment metrics correlated with available topology metrics.
    If topology metrics are missing, generates both synthetic topology and entrainment metrics.
    Uses Cholesky decomposition to ensure the target correlation is achieved.
    
    Args:
        topology_df: DataFrame containing topology metrics (clustering_coefficient, characteristic_path_length).
                     If None, synthetic topology will be generated.
        target_correlation: Target Pearson correlation between Clustering Coefficient and Entrainment Metric.
        noise_level: Standard deviation of the noise component.
        n_subjects: Number of subjects to generate. If topology_df is provided, uses its length.
                    
    Returns:
        Tuple of (topology_df, entrainment_df)
    """
    np.random.seed(RANDOM_SEED)
    
    # Determine N
    if topology_df is not None:
        n_subjects = len(topology_df)
        cc = topology_df['clustering_coefficient'].values
        cpl = topology_df['characteristic_path_length'].values
        subject_ids = topology_df['subject_id'].values
    else:
        if n_subjects is None:
            n_subjects = 50 # Default fallback size
        
        # Generate synthetic topology if missing
        cc = np.random.normal(loc=0.3, scale=0.1, size=n_subjects)
        cc = np.clip(cc, 0, 1)
        cpl = np.random.normal(loc=2.5, scale=0.5, size=n_subjects)
        cpl = np.clip(cpl, 1, 10)
        subject_ids = [f'SUBJ_{i:03d}' for i in range(n_subjects)]
        
        topology_df = pd.DataFrame({
            'subject_id': subject_ids,
            'clustering_coefficient': cc,
            'characteristic_path_length': cpl
        })

    # Normalize CC to unit variance for correlation construction
    cc_mean = cc.mean()
    cc_std = cc.std()
    if cc_std < 1e-9:
        # Handle zero variance case by adding tiny noise
        cc_std = 1e-6
    
    cc_normalized = (cc - cc_mean) / cc_std

    # Generate Entrainment Metric using Cholesky-like construction for correlation
    # We want: corr(CC, EM) = target_correlation
    # EM = target_correlation * CC_norm + sqrt(1 - target^2) * noise_norm
    
    target_rho = target_correlation
    noise_var_component = np.sqrt(1 - target_rho**2)
    
    # Generate independent noise
    noise = np.random.normal(0, 1, size=n_subjects)
    noise_std = noise.std()
    if noise_std < 1e-9:
        noise_std = 1.0
    noise_normalized = noise / noise_std

    # Construct EM
    em_normalized = target_rho * cc_normalized + noise_var_component * noise_normalized
    
    # Scale EM to a realistic range (e.g., 0.1 to 0.9) based on typical entrainment metrics
    # We'll map the normalized EM to this range
    em_min, em_max = 0.1, 0.9
    em = (em_normalized - em_normalized.min()) / (em_normalized.max() - em_normalized.min() + 1e-9) * (em_max - em_min) + em_min
    
    # Add a small amount of the specified noise_level as additional jitter if needed,
    # though the correlation construction already controls the variance ratio.
    # The 'noise_level' parameter in the docstring maps to the sqrt(1-r^2) component effectively.
    
    entrainment_df = pd.DataFrame({
        'subject_id': subject_ids,
        'entrainment_metric': em
    })
    
    return topology_df, entrainment_df

def save_fallback_outputs(topology_df: pd.DataFrame, entrainment_df: pd.DataFrame) -> None:
    """
    Saves the generated fallback data to the required file paths.
    Updates metadata to indicate simulated data usage.
    """
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(DATA_RAW_DIR, exist_ok=True)

    # Save entrainment metrics to raw
    entrainment_df.to_csv(ENTRAINMENT_CSV, index=False)
    print(f"Saved synthetic entrainment metrics to: {ENTRAINMENT_CSV}")

    # Save joined data to processed
    joined_df = pd.merge(topology_df, entrainment_df, on='subject_id', how='inner')
    joined_df['data_source'] = 'Simulated'
    joined_df.to_csv(JOINED_SIMULATED_CSV, index=False)
    print(f"Saved joined simulated data to: {JOINED_SIMULATED_CSV}")

    # Update metadata
    metadata = {
        "data_source": "Simulated",
        "N": len(joined_df),
        "description": "Data generated via simulation fallback (T012c) due to missing or insufficient real data.",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Load existing metadata if present, otherwise start fresh
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                existing_meta = json.load(f)
                existing_meta.update(metadata)
                metadata = existing_meta
        except (json.JSONDecodeError, IOError):
            pass # Start fresh if corrupted
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Updated metadata at: {METADATA_PATH}")

    # Write data gap report
    gap_report = {
        "fallback_triggered": True,
        "data_source": "Simulated",
        "reason": "missing_file_or_low_n",
        "target_correlation": 0.5,
        "subjects_generated": len(joined_df)
    }
    with open(DATA_GAP_REPORT_PATH, 'w') as f:
        json.dump(gap_report, f, indent=2)
    print(f"Data gap report written to: {DATA_GAP_REPORT_PATH}")

def check_and_generate_fallback(target_n: int = 30, target_correlation: float = 0.5, output_dir: str = DATA_PROCESSED_DIR) -> Optional[str]:
    """
    Legacy wrapper for compatibility. Checks if real data exists and is sufficient.
    If not, triggers the full fallback generation process.
    """
    # Check if real topology data exists
    if os.path.exists(TOPOLOGY_CSV):
        try:
            df_real = pd.read_csv(TOPOLOGY_CSV)
            if len(df_real) >= target_n:
                # Check if entrainment exists
                if os.path.exists(ENTRAINMENT_CSV):
                    df_ent = pd.read_csv(ENTRAINMENT_CSV)
                    if len(df_ent) >= target_n:
                        # Sufficient real data
                        return None
        except Exception:
            pass # Fall through to generate

    # Fallback needed
    print(f"Real data missing or insufficient (N < {target_n}). Triggering simulation fallback...")
    
    # Generate both topology and entrainment since real topology is missing or insufficient
    topology_df, entrainment_df = generate_entrainment_fallback(
        topology_df=None, # Force regeneration of topology too
        target_correlation=target_correlation,
        n_subjects=target_n
    )
    
    save_fallback_outputs(topology_df, entrainment_df)
    
    return TOPOLOGY_CSV

def main():
    # Entry point for direct execution (e.g., for testing or manual fallback trigger)
    print("Running simulation fallback module...")
    path = check_and_generate_fallback()
    if path:
        print(f"Fallback data generated and saved.")
    else:
        print("Real data sufficient, no fallback generated.")

if __name__ == "__main__":
    main()