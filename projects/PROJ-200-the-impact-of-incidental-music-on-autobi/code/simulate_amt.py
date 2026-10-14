import pandas as pd
import numpy as np
from pathlib import Path
from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

def main():
    log.info("Simulating AMT data for thin pipeline...")
    root = get_project_root()
    out_path = root / "data" / "raw" / "simulated_amt.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_users = 20
    n_tracks = 50
    
    # Generate users
    users = [f"user_{i}" for i in range(n_users)]
    birth_years = np.random.randint(1970, 2000, size=n_users)
    
    # Generate tracks
    tracks = [f"track_{i}" for i in range(n_tracks)]
    popularity = np.random.uniform(0, 100, size=n_tracks)
    
    data = []
    for i, user in enumerate(users):
        # Each user recalls 3-7 tracks
        user_tracks = np.random.choice(tracks, size=np.random.randint(3, 8), replace=False)
        for track in user_tracks:
            # Simulate a relationship: higher vividness if track is 'popular' (mocking effect)
            track_idx = int(track.split('_')[1])
            pop_effect = popularity[track_idx] / 100.0
            vividness = np.clip(np.random.normal(50 + 20 * pop_effect, 10), 0, 100)
            valence = np.clip(np.random.normal(0 + 2 * pop_effect, 2), -5, 5)
            
            data.append({
                "user_id": user,
                "birth_year": birth_years[i],
                "track_id": track,
                "vividness": vividness,
                "valence": valence,
                "cue": f"Song {track_idx}"
            })
    
    df = pd.DataFrame(data)
    df.to_parquet(out_path)
    log.info(f"Simulated AMT data written to {out_path}")

if __name__ == "__main__":
    main()
