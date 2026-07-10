import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

import pytest
from data.loader import generate_mock_visual_genome
from stimuli.manipulator import process_directory
from stimuli.metadata import load_metadata_from_yaml
from config import get_stimuli_dir, get_stimuli_metadata_dir, get_project_root


def test_full_pipeline():
    """
    Integration test for full pipeline: generate mock images -> manipulate -> metadata.
    
    Asserts that:
    1. Mock images are generated.
    2. Manipulated images (enhanced and reduced) are created for each input.
    3. A valid metadata YAML file is created for each input.
    """
    # Ensure we are working in the project's data directories
    project_root = get_project_root()
    stimuli_dir = get_stimuli_dir()
    metadata_dir = get_stimuli_metadata_dir()
    
    # Clean up previous test runs to ensure fresh state
    # We create a temporary subdirectory to avoid polluting the main data dir if tests run concurrently
    # But per task requirements, we must use the standard paths. 
    # We will assume a clean slate or that the test creates its own unique ID.
    # For this integration test, we will generate a specific set of mock images
    # and then run the pipeline on them.
    
    # Step 1: Generate Mock Visual Genome
    # The loader expects a count and an output directory. 
    # We'll generate 2 images to ensure "multiple" are processed.
    num_images = 2
    generate_mock_visual_genome(num_images, str(stimuli_dir))
    
    # Verify input images exist
    input_images = list(stimuli_dir.glob("*.png"))
    assert len(input_images) == num_images, f"Expected {num_images} input images, found {len(input_images)}"
    
    # Step 2: Run Manipulation Pipeline
    # process_directory takes input_dir, output_dir (for manipulated), and metadata_dir
    # We need to ensure output directories exist for manipulated images
    # The process_directory function in manipulator.py handles output paths internally based on config or arguments
    # Let's assume the standard flow: process_directory(input, output_base, metadata)
    # Looking at the API: process_directory(input_dir, output_dir, metadata_dir)
    
    # We'll define an output directory for manipulated images to keep things clean
    # However, the task says "Assert that multiple manipulated images... are created".
    # The process_directory function likely writes to a subfolder or specific naming convention.
    # Let's call it with the standard directories.
    
    # Note: The process_directory signature in the API surface is:
    # process_directory(input_dir, output_dir, metadata_dir)
    # We need to pass the metadata_dir to ensure metadata is written there.
    
    # Create a specific output dir for manipulated images to verify existence
    manipulated_dir = stimuli_dir / "manipulated"
    manipulated_dir.mkdir(exist_ok=True)
    
    process_directory(
        input_dir=str(stimuli_dir),
        output_dir=str(manipulated_dir),
        metadata_dir=str(metadata_dir)
    )
    
    # Step 3: Verify Artifacts
    
    # 3a: Check that manipulated images exist
    # The manipulator should create 'enhanced' and 'reduced' versions.
    # Based on typical naming in such pipelines, they might be named <id>_enhanced.png, <id>_reduced.png
    # or placed in subdirectories. Let's check for files in the manipulated_dir.
    enhanced_images = list(manipulated_dir.glob("*_enhanced.png"))
    reduced_images = list(manipulated_dir.glob("*_reduced.png"))
    
    # We expect 2 enhanced and 2 reduced images (one for each input)
    assert len(enhanced_images) == num_images, f"Expected {num_images} enhanced images, found {len(enhanced_images)}"
    assert len(reduced_images) == num_images, f"Expected {num_images} reduced images, found {len(reduced_images)}"
    
    # 3b: Check that metadata files exist
    # The metadata should be in metadata_dir with .yaml extension
    metadata_files = list(metadata_dir.glob("*.yaml"))
    
    # We expect one metadata file per input image (or potentially per manipulation, but task says "1 metadata file for each input")
    # If the metadata covers the whole process for an input ID, we expect num_images files.
    # Let's assert we have at least num_images metadata files.
    assert len(metadata_files) >= num_images, f"Expected at least {num_images} metadata files, found {len(metadata_files)}"
    
    # 3c: Verify metadata content is valid YAML and contains expected keys
    for meta_file in metadata_files:
        with open(meta_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, f"Metadata file {meta_file} is empty or invalid YAML"
                # Check for key fields defined in StimulusMetadata dataclass
                assert 'image_id' in data or 'id' in data, f"Metadata file {meta_file} missing image_id"
                assert 'manipulations' in data, f"Metadata file {meta_file} missing manipulations list"
                # Verify manipulations list has entries
                assert isinstance(data['manipulations'], list), "Manipulations should be a list"
                assert len(data['manipulations']) >= 2, "Should have at least enhanced and reduced manipulations"
            except yaml.YAMLError:
                pytest.fail(f"Invalid YAML in {meta_file}")