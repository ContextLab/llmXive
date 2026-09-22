import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import sys

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"BENCH: {message}")

def generate_synthetic_data(n: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic data with required schema for testing.
    Schema: news_exposure_freq, anxiety_score, baseline_anxiety, age, gender, social_media_engagement
    """
    _log_step(f"Generating synthetic data: n={n}, seed={seed}")
    
    np.random.seed(seed)
    
    data = {
        "news_exposure_freq": np.random.normal(5, 2, n),
        "anxiety_score": np.random.normal(10, 3, n),
        "baseline_anxiety": np.random.normal(8, 2.5, n),
        "age": np.random.normal(35, 12, n).astype(int),
        "gender": np.random.choice([0, 1], n),
        "social_media_engagement": np.random.normal(15, 5, n)
    }
    
    # Clip values to reasonable ranges
    df = pd.DataFrame(data)
    df["news_exposure_freq"] = df["news_exposure_freq"].clip(0, 10)
    df["anxiety_score"] = df["anxiety_score"].clip(0, 20)
    df["baseline_anxiety"] = df["baseline_anxiety"].clip(0, 20)
    df["age"] = df["age"].clip(18, 80)
    df["social_media_engagement"] = df["social_media_engagement"].clip(0, 50)
    
    _log_step(f"Generated {len(df)} rows")
    return df

def generate_with_missing_values(df: pd.DataFrame, missing_rate: float = 0.05) -> pd.DataFrame:
    """
    Introduce missing values into the dataframe for testing listwise deletion.
    """
    _log_step(f"Introducing missing values at rate {missing_rate}")
    
    df_missing = df.copy()
    for col in df_missing.columns:
        mask = np.random.rand(len(df_missing)) < missing_rate
        df_missing.loc[mask, col] = np.nan
    
    return df_missing

def main() -> None:
    """Main entry point for benchmark utils script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    df = generate_synthetic_data(n=1000, seed=42)
    output_path = Path("data/raw/benchmark_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")

if __name__ == "__main__":
    import sys
    main()
