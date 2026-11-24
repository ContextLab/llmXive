import json
import os
import shutil
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytest

# The script under test
from code.eye_tracking.parse_fixations import main as run_parse_fixations

@pytest.fixture
def temporary_project(tmp_path: Path):
    """
    Set up a minimal directory structure required by the parser.
    """
    # Create raw eye‑tracking directory
    eye_dir = tmp_path / "data" / "raw" / "ds003123" / "eye_tracking"
    eye_dir.mkdir(parents=True, exist_ok=True)

    # Create interim masks directory
    masks_dir = tmp_path / "data" / "interim" / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy stimulus with simple masks
    stimulus_id = "stim001"
    # 10×10 image – face mask occupies top‑left 2×2 block
    face_mask = np.zeros((10, 10), dtype=np.uint8)
    face_mask[0:2, 0:2] = 255
    weapon_mask = np.zeros((10, 10), dtype=np.uint8)  # empty

    cv2.imwrite(str(masks_dir / f"{stimulus_id}_face.png"), face_mask)
    cv2.imwrite(str(masks_dir / f"{stimulus_id}_weapon.png"), weapon_mask)

    # Create a tiny eye‑tracking CSV for a single participant
    df = pd.DataFrame(
        {
            "trial_id": ["t1", "t1", "t2", "t2"],
            "participant_id": ["p1", "p1", "p1", "p1"],
            "stimulus_id": [stimulus_id, stimulus_id, stimulus_id, stimulus_id],
            "timestamp_ms": [100, 300, 150, 350],
            # First trial: first fixation lands inside the face mask
            "x": [0, 5, 5, 5],
            "y": [0, 5, 5, 5],
            "duration_ms": [50, 70, 60, 80],
        }
    )
    eye_file = eye_dir / "participant1.csv"
    df.to_csv(eye_file, index=False)

    # Return the root path so the test can adjust the llmxive toolkit paths
    return tmp_path

def test_fixation_extraction_produces_valid_csv(monkeypatch, temporary_project):
    """
    End‑to‑end test that the parser creates the expected CSV and
    computes plausible metrics.
    """
    # Point the llmxive toolkit helpers to the temporary location
    # (they resolve paths relative to the current working directory)
    os.chdir(temporary_project)

    # Run the parser
    exit_code = run_parse_fixations()
    assert exit_code == 0, "parse_fixations script should exit with 0"

    # Verify output CSV exists
    csv_path = Path("data") / "interim" / "fixations.csv"
    assert csv_path.is_file(), "fixations.csv should be created"

    df_out = pd.read_csv(csv_path)

    # Expect three ROI rows per trial (face, weapon, background)
    assert len(df_out) == 6, "There should be 2 trials × 3 ROIs = 6 rows"

    # Columns validation
    expected_cols = [
        "trial_id",
        "participant_id",
        "stimulus_id",
        "roi_type",
        "dwell_time_ms",
        "first_fixation_prob",
        "fixation_latency_ms",
    ]
    assert list(df_out.columns) == expected_cols

    # Check that dwell times are non‑negative and latency is either a number or NaN
    assert (df_out["dwell_time_ms"] >= 0).all()
    assert df_out["fixation_latency_ms"].isnull().sum() <= 3  # at most one per ROI may be missing

    # First‑fixation probability should be 0.5 for 'face' (first fixation in face for 1 of 2 trials)
    face_prob = df_out.loc[df_out["roi_type"] == "face", "first_fixation_prob"].iloc[0]
    assert pytest.approx(face_prob, rel=1e-3) == 0.5

    # Background probability should be 0.5 as well (first fixation not in face for the second trial)
    bg_prob = df_out.loc[df_out["roi_type"] == "background", "first_fixation_prob"].iloc[0]
    assert pytest.approx(bg_prob, rel=1e-3) == 0.5

    # Weapon ROI never receives a fixation – dwell time should be 0 for both trials
    weapon_rows = df_out[df_out["roi_type"] == "weapon"]
    assert (weapon_rows["dwell_time_ms"] == 0).all()