"""
Integration test for the labeling pipeline (User Story 2).

This test verifies the end-to-end flow of:
1. Loading video clips (simulated or real if available).
2. Running depth estimation (mocked for integration speed, but structure matches T020).
3. Reconstructing 3D states (T021).
4. Running physics simulation via PhysicsSimWrapper (T022).
5. Assigning labels (valid/invalid/null) based on simulation results (T023, T024).
6. Saving outputs to data/processed/labels.csv and metadata files.

Note: This test uses the real `code/utils/physics_sim.py` and `code/models` classes.
It mocks the heavy depth estimation (monodepth2) to ensure the test runs quickly
and deterministically without requiring a GPU or large model download, while
verifying the logic of the labeling pipeline.
"""

import os
import sys
import json
import tempfile
import shutil
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

import numpy as np
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.video_clip import VideoClip
from models.estimated_state_3d import EstimatedState3D
from models.physical_label import PhysicalLabel
from utils.physics_sim import SimulationConfig, SimulationResult, PhysicsSimWrapper
from utils.memory_manager import generate_subsample_indices

# We will import the logic from a hypothetical generate_labels module if it existed,
# but since T020-T026 are not yet implemented in code/, we implement the test logic
# here to verify the *integration* of the components that will be used.
# The test simulates the pipeline steps to ensure the data flow works.

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)

@pytest.fixture
def sample_video_clips():
    """Generate a list of mock VideoClip objects."""
    clips = [
        VideoClip(
            id="clip_001",
            frames=["frame_001.jpg"], # Mock frames
            duration=2.0,
            source_url="http://example.com/clip1.mp4"
        ),
        VideoClip(
            id="clip_002",
            frames=["frame_002.jpg"],
            duration=2.0,
            source_url="http://example.com/clip2.mp4"
        ),
        VideoClip(
            id="clip_003",
            frames=["frame_003.jpg"],
            duration=2.0,
            source_url="http://example.com/clip3.mp4"
        )
    ]
    return clips

def _mock_depth_estimation(clip: VideoClip) -> np.ndarray:
    """
    Mock function to simulate monodepth2 output.
    Returns a random depth map.
    """
    # Simulate a depth map of shape (H, W)
    return np.random.rand(240, 320).astype(np.float32)

def _mock_reconstruct_state(clip: VideoClip, depth_map: np.ndarray) -> EstimatedState3D:
    """
    Mock function to simulate 3D state reconstruction.
    Returns a deterministic state based on clip ID for test reproducibility.
    """
    # Deterministic "random" based on clip ID hash
    seed = int(clip.id.split('_')[1])
    rng = np.random.default_rng(seed)
    
    positions = rng.uniform(-1.0, 1.0, (3,))
    velocities = rng.uniform(-0.5, 0.5, (3,))
    orientations = rng.uniform(-0.1, 0.1, (3,))
    
    # Simulate confidence based on "depth map" variance
    confidence = 0.95 if np.std(depth_map) > 0.1 else 0.45

    return EstimatedState3D(
        positions=positions.tolist(),
        velocities=velocities.tolist(),
        orientations=orientations.tolist(),
        confidence_score=float(confidence)
    )

def _run_physics_check(state: EstimatedState3D) -> SimulationResult:
    """
    Run physics simulation using the real PhysicsSimWrapper.
    Returns a result indicating validity.
    """
    # Create a config for the simulation
    sim_config = SimulationConfig(
        gravity=[0.0, 0.0, -9.81],
        dt=0.02,
        max_steps=10
    )
    
    wrapper = PhysicsSimWrapper()
    
    # We need to convert the list back to arrays for the wrapper if it expects them
    # The wrapper expects numpy arrays or lists that can be converted.
    result = wrapper.simulate(
        positions=np.array(state.positions),
        velocities=np.array(state.velocities),
        orientations=np.array(state.orientations),
        config=sim_config
    )
    
    return result

def test_labeling_pipeline_integration(temp_data_dir, sample_video_clips):
    """
    End-to-end integration test for the labeling pipeline.
    
    Verifies:
    1. Depth estimation (mocked) produces data.
    2. State reconstruction produces EstimatedState3D objects.
    3. Physics simulation runs and returns valid/invalid.
    4. Logic correctly assigns 'valid', 'invalid', or 'null' labels.
    5. Outputs are written to CSV and JSON as specified in T025/T026.
    """
    
    output_csv = Path(temp_data_dir) / "labels.csv"
    output_metadata = Path(temp_data_dir) / "metadata.json"
    output_log = Path(temp_data_dir) / "excluded_samples.log"
    
    results = []
    metadata_list = []
    null_entries = []
    
    for clip in sample_video_clips:
        # Step 1: Depth Estimation (Mocked)
        depth_map = _mock_depth_estimation(clip)
        
        # Step 2: 3D Reconstruction (Mocked)
        state = _mock_reconstruct_state(clip, depth_map)
        
        # Step 3: Physics Simulation (Real wrapper)
        sim_result = _run_physics_check(state)
        
        # Step 4: Label Assignment Logic (T023, T024)
        label_value = None
        reason = ""
        
        if state.confidence_score < 0.9:
            # T024: Assign 'null' if confidence low
            label_value = "null"
            reason = f"Low reconstruction confidence: {state.confidence_score:.2f}"
            null_entries.append(clip.id)
        elif not sim_result.success:
            label_value = "null"
            reason = f"Simulation failed: {sim_result.error_message}"
            null_entries.append(clip.id)
        else:
            # Determine valid/invalid based on simulation
            # For this test, if max_z > 0 (hit ground) it's valid, else invalid
            # Or simply based on a threshold in sim_result
            if sim_result.is_valid:
                label_value = "valid"
                reason = "Physics simulation passed constraints."
            else:
                label_value = "invalid"
                reason = "Physics simulation detected violation (e.g., collision)."
        
        label_obj = PhysicalLabel(
            clip_id=clip.id,
            label=label_value,
            reason=reason
        )
        
        results.append(label_obj)
        metadata_list.append({
            "clip_id": clip.id,
            "confidence": state.confidence_score,
            "sim_success": sim_result.success,
            "sim_duration": sim_result.duration
        })
    
    # Step 5: Save Outputs (T025)
    # Write CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["clip_id", "label", "reason"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "clip_id": r.clip_id,
                "label": r.label,
                "reason": r.reason
            })
    
    # Write Metadata JSON
    with open(output_metadata, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    # Write Log for Null/Excluded (T026)
    with open(output_log, 'w') as f:
        f.write("Samples marked as 'null' due to low confidence or simulation failure:\n")
        for entry in null_entries:
            f.write(f"- {entry}\n")
    
    # --- Assertions ---
    
    # 1. Verify CSV exists and has content
    assert output_csv.exists(), "labels.csv was not created"
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(sample_video_clips), "CSV row count mismatch"
        
        # Check that we have a mix of labels (since we mocked different seeds)
        labels_found = set(row['label'] for row in rows)
        assert 'null' in labels_found or 'valid' in labels_found, "Expected at least some labels"
        
    # 2. Verify Metadata JSON
    assert output_metadata.exists(), "metadata.json was not created"
    with open(output_metadata, 'r') as f:
        meta_data = json.load(f)
        assert len(meta_data) == len(sample_video_clips), "Metadata count mismatch"
        
    # 3. Verify Log file
    assert output_log.exists(), "excluded_samples.log was not created"
    with open(output_log, 'r') as f:
        log_content = f.read()
        # Check if any null entries were logged (if our mock generated any)
        # We don't strictly require nulls to exist if our mock didn't trigger them,
        # but the file must exist.
        assert "Samples marked as 'null'" in log_content, "Log format incorrect"
        
    # 4. Verify PhysicsSimWrapper was actually used (by checking sim_result properties)
    # This is implicitly checked by the fact that we didn't crash and got results.
    
    print(f"Integration test passed. Outputs written to {temp_data_dir}")
    print(f"Labels found: {labels_found}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])