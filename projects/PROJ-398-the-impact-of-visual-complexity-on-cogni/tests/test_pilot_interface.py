import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd
from PIL import Image

# Import the functions we just implemented
from src.experiment.pilot_interface import (
    ensure_output_dir,
    list_stimuli_images,
    load_existing_ratings,
    append_rating,
    main,
)

@pytest.fixture
def temp_stimuli_dir():
    """Create a temporary directory with a few dummy image files."""
    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        # Create three tiny PNG images
        for i in range(3):
            img_path = dir_path / f"stimulus_{i}.png"
            # Use Pillow to create a 1x1 white pixel image
            Image.new("RGB", (1, 1), color="white").save(img_path)
        yield dir_path

@pytest.fixture
def temp_rating_file():
    """Temporary path for the ratings CSV."""
    with tempfile.TemporaryDirectory() as td:
        rating_path = Path(td) / "ratings.csv"
        yield rating_path

def test_ensure_output_dir(tmp_path):
    target = tmp_path / "nested" / "output.csv"
    # Function should create the parent directory
    ensure_output_dir(target)
    assert target.parent.is_dir()

def test_list_stimuli_images(temp_stimuli_dir):
    images = list_stimuli_images(temp_stimuli_dir)
    assert len(images) == 3
    # Ensure the returned paths are inside the temporary directory
    for img in images:
        assert img.parent == temp_stimuli_dir

def test_append_and_load_ratings(temp_rating_file):
    # Append a couple of rows
    append_rating(temp_rating_file, "stimulus_0", "p1", 4.0)
    append_rating(temp_rating_file, "stimulus_1", "p2", 5.5)

    df = load_existing_ratings(temp_rating_file)
    assert len(df) == 2
    assert set(df["image_id"]) == {"stimulus_0", "stimulus_1"}
    assert df.loc[df["image_id"] == "stimulus_0", "complexity_score"].iloc[0] == 4.0

def test_load_existing_ratings_when_missing(temp_rating_file):
    # No file yet – should return an empty DataFrame with proper columns
    df = load_existing_ratings(temp_rating_file)
    assert df.empty
    assert list(df.columns) == ["image_id", "participant_id", "complexity_score"]

def test_end_to_end_flow(monkeypatch, temp_stimuli_dir, temp_rating_file):
    """
    Run the Streamlit app in TEST_MODE so it writes dummy ratings automatically.
    Verify that the CSV is created and contains the expected number of rows.
    """
    # Point the app to the temporary directories/files via environment variables
    monkeypatch.setenv("STIMULI_DIR", str(temp_stimuli_dir))
    monkeypatch.setenv("RATINGS_PATH", str(temp_rating_file))
    monkeypatch.setenv("COHORT_PATH", str(temp_stimuli_dir / "cohort.json"))
    monkeypatch.setenv("TEST_MODE", "1")

    # Create a minimal cohort file so the app can load it
    cohort = [{"participant_id": "test_participant"}]
    with open(os.getenv("COHORT_PATH"), "w", encoding="utf-8") as f:
        import json
        json.dump(cohort, f)

    # Run the main function – it should execute without raising and write the CSV
    main()

    # Verify the output CSV
    df = pd.read_csv(temp_rating_file)
    # One dummy rating per stimulus image
    assert len(df) == len(list(temp_stimuli_dir.glob("*.png")))
    assert set(df["participant_id"]) == {"test_participant"}
    assert all(df["complexity_score"] == 5.0)