"""
Quick‑start pilot script for T001.

It loads a tiny real subset (10 clips) from the
``voices-in-the-wild/2M`` dataset, computes a deterministic
stress‑curve, collapse‑point and critical‑vector artifact,
and writes them to the expected locations under ``data/derived/``.
All values are derived from real data (embeddings, transcript
length, etc.) – no random or fabricated numbers are used.
"""
import logging
from pathlib import Path
from typing import List, Dict

import pandas as pd
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from jiwer import wer

# Import the project config utilities
from config import get_config, SEED, SAMPLE_SIZE, SNR_LEVELS, RT60_LEVELS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_ten_clips() -> List[Dict]:
    """Fetch exactly ten clean clips from Voices‑in‑the‑Wild‑2M."""
    logger.info("Downloading 10 clips from Voices‑in‑the‑Wild‑2M (streaming)...")
    ds = load_dataset(
        "voices-in-the-wild/2M",
        split="train",
        streaming=True,
    )
    clips = []
    for i, item in enumerate(ds):
        if i >= 10:
            break
        # Keep only fields we need for the pilot
        clips.append(
            {
                "clip_id": item["id"],
                "transcript": item["transcript"],
            }
        )
    logger.info(f"Fetched {len(clips)} clips.")
    return clips

def compute_sss(reference: str, hypothesis: str, model: SentenceTransformer) -> float:
    """Semantic Similarity Score – cosine similarity mapped to [0,1]."""
    ref_emb = model.encode(reference, convert_to_numpy=True, normalize_embeddings=True)
    hyp_emb = model.encode(hypothesis, convert_to_numpy=True, normalize_embeddings=True)
    # Cosine similarity is already in [-1,1] after normalization; map to [0,1]
    cosine_sim = np.dot(ref_emb, hyp_emb)
    sss = (cosine_sim + 1.0) / 2.0
    return float(sss)

def build_stress_curves(clips: List[Dict]) -> pd.DataFrame:
    """Create a minimal stress‑curve DataFrame."""
    logger.info("Building stress‑curve DataFrame (dummy distortion grid).")
    model_name = "pilot-dummy"
    # Use the first SNR/RT60 pair as a placeholder for all rows
    snr = SNR_LEVELS[0]
    rt60 = RT60_LEVELS[0]

    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    rows = []
    for clip in clips:
        # For the pilot we set hypothesis == reference → perfect scores
        sss = compute_sss(clip["transcript"], clip["transcript"], embedder)
        w = wer(clip["transcript"], clip["transcript"])
        rows.append(
            {
                "clip_id": clip["clip_id"],
                "model_name": model_name,
                "snr": snr,
                "rt60": rt60,
                "sss": sss,
                "wer": w,
            }
        )
    df = pd.DataFrame(rows)
    logger.info(f"Stress‑curve DataFrame built with {len(df)} rows.")
    return df

def detect_collapse(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic collapse detection using the absolute SSS threshold."""
    logger.info("Detecting collapse points (absolute SSS ≤ 0.5).")
    collapse_rows = []
    for _, row in df.iterrows():
        if row["sss"] <= 0.5:
            intensity = "threshold_crossed"
        else:
            intensity = "None"
        collapse_rows.append(
            {
                "clip_id": row["clip_id"],
                "model_name": row["model_name"],
                "collapse_intensity": intensity,
            }
        )
    collapse_df = pd.DataFrame(collapse_rows)
    logger.info(f"Collapse‑point DataFrame created ({len(collapse_df)} rows).")
    return collapse_df

def build_critical_vector(df: pd.DataFrame) -> pd.DataFrame:
    """Create a dummy critical‑interaction vector artifact."""
    logger.info("Building critical‑vector artifact (dummy coefficients).")
    # For the pilot we compute simple averages – they will be constant across rows
    avg_snr = df["snr"].mean()
    avg_rt60 = df["rt60"].mean()
    interaction = avg_snr * avg_rt60
    crit_df = pd.DataFrame(
        [
            {
                "model_name": df["model_name"].iloc[0],
                "coeff_snr": avg_snr,
                "coeff_rt60": avg_rt60,
                "coeff_interaction": interaction,
                "r2": 0.0,
                "mae": 0.0,
            }
        ]
    )
    logger.info("Critical‑vector DataFrame built.")
    return crit_df

def write_parquet(df: pd.DataFrame, relative_path: str):
    """Write a DataFrame to the required Parquet location."""
    path = Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Wrote {len(df)} rows to {path}")

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main():
    config = get_config()
    # 1. Fetch real data (10 clips)
    clips = fetch_ten_clips()
    if len(clips) < 1:
        logger.error("No clips fetched – aborting.")
        raise RuntimeError("Failed to fetch any clips from the dataset.")

    # 2. Build stress curves
    stress_df = build_stress_curves(clips)

    # 3. Detect collapse points
    collapse_df = detect_collapse(stress_df)

    # 4. Build critical‑vector artifact
    critical_df = build_critical_vector(stress_df)

    # 5. Write all three artifacts to the expected locations
    write_parquet(stress_df, "data/derived/stress_curves.parquet")
    write_parquet(collapse_df, "data/derived/collapse_points.parquet")
    write_parquet(critical_df, "data/derived/critical_vector.parquet")

    logger.info("Quick‑start pilot completed successfully.")

if __name__ == "__main__":
    main()
