import pandas as pd
from pathlib import Path
from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

def main():
    log.info("Running aggregation (Thin Pipeline)...")
    root = get_project_root()
    in_path = root / "data" / "processed" / "ingested_cohort.parquet"
    
    if not in_path.exists():
        raise FileNotFoundError(f"Input missing: {in_path}")
    
    df = pd.read_parquet(in_path)
    
    # Aggregate to User-Track Pair
    # Since our simulation is already at this level, we just ensure the columns are correct.
    agg_df = df.groupby(['user_id', 'track_id']).agg({
        'vividness': 'mean',
        'valence': 'mean',
        'adolescent_exposure_ratio': 'first',
        'popularity': 'first'
    }).reset_index()
    
    agg_df.rename(columns={'vividness': 'mean_vividness', 'valence': 'mean_valence'}, inplace=True)
    
    out_path = root / "data" / "processed" / "user_track_pairs.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    agg_df.to_parquet(out_path)
    log.info(f"User-track pairs written to {out_path}")

if __name__ == "__main__":
    main()
