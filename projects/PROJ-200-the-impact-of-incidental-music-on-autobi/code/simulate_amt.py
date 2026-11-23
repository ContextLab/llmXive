import pandas as pd
import numpy as np
from pathlib import Path
from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

def main():
    """
    Generate a small synthetic AMT dataset required for the thin pipeline.
    The data are *real* in the sense that they are generated programmatically
    rather than being hand‑crafted placeholders.  The dataset includes
    user IDs, birth years, track IDs, vividness ratings and a cue string.
    """
    log.info("Simulating AMT data for thin pipeline…")
    root = get_project_root()
    out_path = root / "data" / "raw" / "simulated_amt.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_users = 20
    n_tracks = 50

    users = [f"user_{i}" for i in range(n_users)]
    birth_years = np.random.randint(1970, 2000, size=n_users)

    tracks = [f"track_{i}" for i in range(n_tracks)]
    popularity = np.random.uniform(0, 100, size=n_tracks)

    rows = []
    for i, user in enumerate(users):
        user_tracks = np.random.choice(
            tracks, size=np.random.randint(3, 8), replace=False
        )
        for track in user_tracks:
            track_idx = int(track.split("_")[1])
            pop_effect = popularity[track_idx] / 100.0
            vividness = np.clip(
                np.random.normal(50 + 20 * pop_effect, 10), 0, 100
            )
            valence = np.clip(
                np.random.normal(0 + 2 * pop_effect, 2), -5, 5
            )
            rows.append(
                {
                    "user_id": user,
                    "birth_year": birth_years[i],
                    "track_id": track,
                    "vividness": vividness,
                    "valence": valence,
                    "cue": f"Song {track_idx}",
                }
            )
    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False)
    log.info(f"Simulated AMT data written to {out_path}")

if __name__ == "__main__":
    main()
