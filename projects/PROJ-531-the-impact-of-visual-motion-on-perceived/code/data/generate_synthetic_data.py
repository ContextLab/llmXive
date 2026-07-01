import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

def generate_synthetic_data(n_samples: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic human-avatar interaction data with known ground-truth
    motion-agency relationships (FR-011).

    This generator is used ONLY if T012 (real data download) fails or returns
    "unavailable"/"invalid".

    Features:
    - latency: Interaction latency in ms (0-500ms)
    - smoothness: Jerk metric normalized (0-1, higher is smoother)
    - lead_time: Predictive lead time in ms (-100 to 200ms)
    - user_response_trigger: Distinct from agency score (FR-012)
    - agency_score: Perceived agency score (0-100)

    Ground-truth relationships:
    - Agency increases with smoother motion (positive correlation with smoothness)
    - Agency decreases with higher latency (negative correlation with latency)
    - Agency increases with positive lead_time (predictive motion)
    - User response trigger is independent noise to ensure distinctness (FR-012)
    """
    np.random.seed(seed)

    # Generate base features
    latency = np.random.normal(loc=150, scale=80, size=n_samples)
    latency = np.clip(latency, 0, 500)

    smoothness = np.random.beta(a=2, b=5, size=n_samples)  # Skewed towards lower smoothness
    smoothness = np.clip(smoothness, 0, 1)

    lead_time = np.random.normal(loc=50, scale=60, size=n_samples)
    lead_time = np.clip(lead_time, -100, 200)

    # User response trigger (distinct from agency score per FR-012)
    # This represents a separate behavioral metric
    user_response_trigger = np.random.normal(loc=0.5, scale=0.2, size=n_samples)
    user_response_trigger = np.clip(user_response_trigger, 0, 1)

    # Generate agency score with known ground-truth relationships (FR-011)
    # Agency = f(smoothness, latency, lead_time) + noise
    # Weights chosen to create realistic but known correlations
    agency_score = (
        30 * smoothness -  # Positive correlation with smoothness
        0.1 * latency +     # Negative correlation with latency
        0.15 * lead_time +  # Positive correlation with lead_time
        np.random.normal(0, 5, size=n_samples)  # Random noise
    )

    # Scale agency to 0-100 range
    agency_score = np.clip(agency_score, 0, 100)

    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': [f'P{str(i).zfill(4)}' for i in range(n_samples)],
        'latency': np.round(latency, 2),
        'smoothness': np.round(smoothness, 4),
        'lead_time': np.round(lead_time, 2),
        'user_response_trigger': np.round(user_response_trigger, 4),
        'agency_score': np.round(agency_score, 2)
    })

    return df

def main():
    """
    Main entry point for synthetic data generation.
    Checks if real data is available; if not, generates synthetic data.
    """
    # Define paths
    raw_dir = Path('data/raw')
    processed_dir = Path('data/processed')
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Check if real data is available (T012 output)
    download_status_path = raw_dir / 'download_status.json'
    use_synthetic = True

    if download_status_path.exists():
        with open(download_status_path, 'r') as f:
            status_data = json.load(f)
            if status_data.get('status') in ['available', 'valid']:
                use_synthetic = False
                print("Real data is available. Skipping synthetic generation.")
                # We still create a marker to indicate we checked
                marker_path = processed_dir / 'synthetic_data_status.json'
                with open(marker_path, 'w') as f:
                    json.dump({
                        'status': 'skipped',
                        'reason': 'Real data available',
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2)
                return

    # Generate synthetic data
    print("Real data unavailable or invalid. Generating synthetic data...")
    df = generate_synthetic_data(n_samples=150, seed=42)

    # Save to processed directory
    output_path = processed_dir / 'cleaned_data.csv'
    df.to_csv(output_path, index=False)

    # Save metadata
    metadata = {
        'source': 'synthetic_generator',
        'n_samples': len(df),
        'ground_truth_relationships': {
            'latency': 'negative_correlation',
            'smoothness': 'positive_correlation',
            'lead_time': 'positive_correlation'
        },
        'distinct_user_trigger': True,
        'timestamp': datetime.now().isoformat()
    }

    metadata_path = processed_dir / 'synthetic_data_status.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Generated {len(df)} synthetic samples.")
    print(f"Output saved to: {output_path}")
    print(f"Metadata saved to: {metadata_path}")

if __name__ == '__main__':
    main()
