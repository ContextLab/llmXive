"""
Integration test for the alignment step (T007).

The test builds a minimal synthetic dataset that mimics the
outputs of the earlier pipeline stages.  It then runs the
``code.analysis.align_data`` script and validates that the
resulting CSV conforms to the JSON schema defined in
``contracts/dataset.schema.yaml`` and that the statistics JSON
correctly reflects the number of rows and exclusions.
"""

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths
from code.analysis import align_data

# Load the JSON schema for a single row (the schema validates a list of rows)
SCHEMA_PATH = Path("specs/001-the-influence-of-visual-salience-on-atte/contracts/dataset.schema.yaml")
with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    ROW_SCHEMA = json.load(f)

@pytest.fixture
def minimal_dataset(tmp_path: Path):
    """
    Create a minimal but realistic set of input artifacts:

    - One stimulus image (id: ``stim1``) with a salience map.
    - Corresponding ``face`` and ``weapon`` masks.
    - Low‑level feature JSON.
    - A small fixation CSV with two trials (face and weapon ROIs).
    """
    # ------------------------------------------------------------------
    # Directories
    # ------------------------------------------------------------------
    # Use the toolkit helpers so that the temporary root is respected.
    # The fixture patches ``paths.root`` to the temporary directory.
    from llmxive_toolkit import get_logger, paths as toolkit_paths
    toolkit_paths.root = tmp_path

    # Create required folders
    (paths.interim("salience_maps")).mkdir(parents=True, exist_ok=True)
    (paths.interim("masks")).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Salience map (simple gradient)
    # ------------------------------------------------------------------
    import numpy as np
    sal_map = np.linspace(0, 1, 100).reshape((10, 10)).astype(np.float32)
    sal_path = paths.interim("salience_maps", "stim1.npy")
    np.save(sal_path, sal_map)

    # ------------------------------------------------------------------
    # Masks (binary squares)
    # ------------------------------------------------------------------
    import cv2
    mask_face = np.zeros((10, 10), dtype=np.uint8)
    mask_face[2:6, 2:6] = 255
    mask_weapon = np.zeros((10, 10), dtype=np.uint8)
    mask_weapon[6:9, 6:9] = 255
    cv2.imwrite(str(paths.interim("masks", "stim1_face.png")), mask_face)
    cv2.imwrite(str(paths.interim("masks", "stim1_weapon.png")), mask_weapon)

    # ------------------------------------------------------------------
    # Low‑level features JSON
    # ------------------------------------------------------------------
    low_features = {
        "stim1": {
            "luminance": 128.0,
            "contrast": 30.5,
            "edge_density": 0.12,
            "scene_complexity": 5,
        }
    }
    low_feat_path = paths.interim("low_level_features.json")
    low_feat_path.write_text(json.dumps(low_features))

    # ------------------------------------------------------------------
    # Fixation CSV
    # ------------------------------------------------------------------
    fixation_rows = [
        {
            "trial_id": "t1",
            "participant_id": "p1",
            "stimulus_id": "stim1",
            "roi_type": "face",
            "dwell_time_ms": 350,
            "first_fixation_prob": 0.8,
            "fixation_latency_ms": 120,
        },
        {
            "trial_id": "t2",
            "participant_id": "p1",
            "stimulus_id": "stim1",
            "roi_type": "weapon",
            "dwell_time_ms": 210,
            "first_fixation_prob": 0.3,
            "fixation_latency_ms": 200,
        },
    ]
    fixation_df = pd.DataFrame(fixation_rows)
    fixation_path = paths.interim("fixations.csv")
    fixation_df.to_csv(fixation_path, index=False)

    return {
        "salience_map": sal_path,
        "masks_dir": paths.interim("masks"),
        "low_feat_path": low_feat_path,
        "fixation_path": fixation_path,
    }

def test_alignment_produces_valid_output(minimal_dataset):
    """
    Run the alignment script and validate the outputs.
    """
    # Execute the script
    assert align_data.main() == 0

    # ------------------------------------------------------------------
    # Validate CSV structure against the row schema
    # ------------------------------------------------------------------
    aligned_csv = paths.processed("aligned_data.csv")
    assert aligned_csv.is_file(), "aligned_data.csv was not created"

    df = pd.read_csv(aligned_csv)

    # Every row must contain all required columns
    required_cols = set(ROW_SCHEMA["required"])
    assert required_cols.issubset(df.columns), "Missing required columns in CSV"

    # Validate each row against the JSON schema (convert row to dict)
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        # jsonschema expects proper types; pandas may give np.int64 etc.,
        # which are JSON‑serialisable, so we cast to native Python types.
        for k, v in row_dict.items():
            if isinstance(v, (np.integer, np.floating)):
                row_dict[k] = v.item()
        try:
            validate(instance=row_dict, schema=ROW_SCHEMA)
        except ValidationError as ve:
            pytest.fail(f"Row failed schema validation: {ve}")

    # ------------------------------------------------------------------
    # Validate statistics JSON
    # ------------------------------------------------------------------
    stats_path = paths.processed("alignment_stats.json")
    assert stats_path.is_file(), "alignment_stats.json was not created"
    stats = json.loads(stats_path.read_text())

    assert stats["total_rows"] == len(df)
    # In this minimal dataset all components exist, so no rows should be excluded
    assert stats["excluded_rows"] == df["excluded"].sum() == 0
    assert stats["exclusion_rate"] == 0.0
    # Reason breakdown should be empty (no exclusions)
    assert stats["reason_breakdown"] == {}

def test_exclusion_handling(tmp_path: Path):
    """
    Verify that rows with missing components are flagged as excluded
    and that the statistics reflect the correct reasons.
    """
    # Patch the toolkit root to the temporary directory
    from llmxive_toolkit import paths as toolkit_paths
    toolkit_paths.root = tmp_path

    # Create minimal required folders
    (paths.interim("salience_maps")).mkdir(parents=True, exist_ok=True)
    (paths.interim("masks")).mkdir(parents=True, exist_ok=True)

    # Create a salience map for stimulus ``stimX`` but *no* mask for weapon ROI
    import numpy as np, cv2, pandas as pd
    sal_map = np.zeros((5, 5), dtype=np.float32)
    np.save(paths.interim("salience_maps", "stimX.npy"), sal_map)

    # Only a face mask exists
    face_mask = np.ones((5, 5), dtype=np.uint8) * 255
    cv2.imwrite(str(paths.interim("masks", "stimX_face.png")), face_mask)

    # Low‑level features present
    low_features = {
        "stimX": {
            "luminance": 100.0,
            "contrast": 20.0,
            "edge_density": 0.05,
            "scene_complexity": 3,
        }
    }
    paths.interim("low_level_features.json").write_text(json.dumps(low_features))

    # Fixation CSV with two rows (face and weapon)
    fixation_df = pd.DataFrame([
        {
            "trial_id": "tF",
            "participant_id": "pA",
            "stimulus_id": "stimX",
            "roi_type": "face",
            "dwell_time_ms": 150,
            "first_fixation_prob": 0.6,
            "fixation_latency_ms": 80,
        },
        {
            "trial_id": "tW",
            "participant_id": "pA",
            "stimulus_id": "stimX",
            "roi_type": "weapon",
            "dwell_time_ms": 200,
            "first_fixation_prob": 0.2,
            "fixation_latency_ms": 120,
        },
    ])
    fixation_df.to_csv(paths.interim("fixations.csv"), index=False)

    # Run alignment
    assert align_data.main() == 0

    # Load outputs
    aligned_df = pd.read_csv(paths.processed("aligned_data.csv"))
    stats = json.loads(paths.processed("alignment_stats.json").read_text())

    # The weapon row should be excluded because its mask is missing
    weapon_row = aligned_df[aligned_df["roi_type"] == "weapon"].iloc[0]
    assert weapon_row["excluded"] is True

    # The face row should be included
    face_row = aligned_df[aligned_df["roi_type"] == "face"].iloc[0]
    assert face_row["excluded"] is False

    # Statistics must reflect one excluded row
    assert stats["total_rows"] == 2
    assert stats["excluded_rows"] == 1
    assert stats["exclusion_rate"] == 0.5
    # Reason breakdown should contain the key we used for missing mask/salience
    assert "missing_salience_or_mask" in stats["reason_breakdown"]
    # No missing low‑level features in this case
    assert "missing_low_level_features" not in stats["reason_breakdown"]