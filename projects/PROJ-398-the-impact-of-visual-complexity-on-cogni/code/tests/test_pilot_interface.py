"""
Integration tests for the pilot interface.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from PIL import Image
import numpy as np

from src.config import DATA_DIR
from src.experiment.pilot_interface import (
    ensure_output_dir,
    list_stimuli_images,
    append_rating,
    load_existing_ratings,
    main
)


@pytest.fixture
def temp_stimuli_dir():
    """Create a temporary stimuli directory with test images."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        stimuli_path = Path(tmp_dir) / "stimuli" / "raw"
        stimuli_path.mkdir(parents=True, exist_ok=True)

        # Create test images
        for i in range(3):
            img = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
            img.save(stimuli_path / f"test_image_{i}.png")

        # Temporarily override the global constant
        original_stimuli_dir = None
        import src.experiment.pilot_interface as pilot_module
        original_stimuli_dir = pilot_module.STIMULI_DIR
        pilot_module.STIMULI_DIR = stimuli_path

        yield stimuli_path

        # Restore original
        pilot_module.STIMULI_DIR = original_stimuli_dir


@pytest.fixture
def temp_rating_file():
    """Create a temporary rating file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        rating_path = Path(tmp_dir) / "measurements" / "human_ratings.csv"
        rating_path.parent.mkdir(parents=True, exist_ok=True)

        original_rating_file = None
        import src.experiment.pilot_interface as pilot_module
        original_rating_file = pilot_module.RATING_FILE
        pilot_module.RATING_FILE = rating_path

        yield rating_path

        pilot_module.RATING_FILE = original_rating_file


def test_ensure_output_dir(temp_rating_file):
    """Test that ensure_output_dir creates the directory if missing."""
    # Remove the directory
    temp_rating_file.parent.rmdir()

    # Call the function
    ensure_output_dir()

    # Verify directory exists
    assert temp_rating_file.parent.exists()


def test_list_stimuli_images(temp_stimuli_dir):
    """Test that list_stimuli_images returns the correct images."""
    images = list_stimuli_images()

    assert len(images) == 3
    assert all(img.suffix in {'.png', '.jpg', '.jpeg'} for img in images)
    assert all(img.parent == temp_stimuli_dir for img in images)


def test_append_rating(temp_rating_file, temp_stimuli_dir):
    """Test that append_rating correctly writes to CSV."""
    image_id = "test_image_0.png"
    participant_id = "P001"
    complexity_score = 5

    append_rating(image_id, participant_id, complexity_score)

    # Verify file exists and content is correct
    assert temp_rating_file.exists()
    df = pd.read_csv(temp_rating_file)
    assert len(df) == 1
    assert df.iloc[0]['image_id'] == image_id
    assert df.iloc[0]['participant_id'] == participant_id
    assert df.iloc[0]['complexity_score'] == complexity_score


def test_load_existing_ratings(temp_rating_file, temp_stimuli_dir):
    """Test loading existing ratings from CSV."""
    # First, add a rating
    append_rating("test_image_1.png", "P002", 3)

    # Then load it
    df = load_existing_ratings()

    assert len(df) == 1
    assert df.iloc[0]['participant_id'] == "P002"
    assert df.iloc[0]['complexity_score'] == 3


def test_end_to_end_flow(temp_stimuli_dir, temp_rating_file):
    """
    Integration test simulating the end-to-end flow of the pilot interface.
    This test verifies:
    1. Images are listed correctly
    2. Ratings can be appended
    3. Existing ratings are loaded and filtered correctly
    """
    # Simulate participant P001 rating two images
    append_rating("test_image_0.png", "P001", 4)
    append_rating("test_image_1.png", "P001", 6)

    # Verify ratings were saved
    df = load_existing_ratings()
    p001_ratings = df[df['participant_id'] == 'P001']
    assert len(p001_ratings) == 2

    # Simulate listing images for P001 (should exclude already rated)
    all_images = list_stimuli_images()
    rated_images = set(p001_ratings['image_id'])
    pending_images = [img for img in all_images if img.name not in rated_images]

    # Should have 1 image left (test_image_2.png)
    assert len(pending_images) == 1
    assert pending_images[0].name == "test_image_2.png"

    # P002 should see all 3 images
    p002_ratings = df[df['participant_id'] == 'P002']
    assert len(p002_ratings) == 0  # No ratings yet

    all_images = list_stimuli_images()
    rated_images_p002 = set(
        df[df['participant_id'] == 'P002']['image_id']
    )
    pending_images_p002 = [img for img in all_images if img.name not in rated_images_p002]
    assert len(p002_pending_images) == 3

    # P002 rates one image
    append_rating("test_image_0.png", "P002", 2)
    df = load_existing_ratings()
    p002_ratings = df[df['participant_id'] == 'P002']
    assert len(p002_ratings) == 1
    assert p002_ratings.iloc[0]['complexity_score'] == 2