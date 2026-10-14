import pandas as pd
import numpy as np
from pathlib import Path
from config import get_project_root
from utils import get_logger
import simulate_amt

log = get_logger(__name__)

def main():
    log.info("Running data ingestion (Thin Pipeline)...")
    # Ensure simulated data exists
    simulate_amt.main()
    
    root = get_project_root()
    raw_path = root / "data" / "raw" / "simulated_amt.parquet"
    df = pd.read_parquet(raw_path)
    
    # In a real scenario, we would join with MSD listening logs.
    # For the thin pipeline, we simulate the 'adolescent_exposure_ratio' and 'popularity'.
    np.random.seed(42)
    df['adolescent_exposure_ratio'] = np.random.beta(2, 5, size=len(df))
    df['popularity'] = np.random.uniform(0, 100, size=len(df))
    
    out_path = root / "data" / "processed" / "ingested_cohort.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
    log.info(f"Ingested cohort written to {out_path}")

if __name__ == "__main__":
    main()
