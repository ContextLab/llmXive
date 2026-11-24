import pandas as pd
from pathlib import Path
from config import get_project_root
from utils import get_logger, write_parquet

log = get_logger(__name__)

def main():
    log.info("Running thin aggregation...")
    root = get_project_root()
    input_path = root / "data" / "processed" / "ingested_cohort.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Missing {input_path}")
    
    df = pd.read_parquet(input_path)
    # Ensure columns match contract: user_id, track_id, adolescent_exposure_score, popularity, mean_vividness
    # The ingestion step already produced these.
    df = df.dropna(subset=["mean_vividness", "adolescent_exposure_score"])
    
    out_path = root / "data" / "processed" / "user_track_pairs.parquet"
    write_parquet(df, out_path)
    log.info(f"User-track pairs written to {out_path}")

if __name__ == "__main__":
    main()
