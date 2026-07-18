import json
import os
import pytest
import numpy as np

from code.data_generation import TopologyShiftGenerator
from code.utils import compute_sha256


class TestTopologyShiftGenerator:
    def test_output_directory_exists(self, tmp_path):
        """Test that the output directory is created."""
        output_dir = str(tmp_path / "generated")
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=2,
            seed=42,
            steps_per_trajectory=10,
        )
        generator.generate_dataset()

        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "metadata.json"))

    def test_trajectory_files_created(self, tmp_path):
        """Test that trajectory files are created for each topology."""
        output_dir = str(tmp_path / "generated")
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=3,
            seed=42,
            steps_per_trajectory=10,
        )
        generator.generate_dataset()

        for i in range(3):
            trajectory_file = os.path.join(output_dir, f"trajectory_{i:04d}.json")
            assert os.path.exists(trajectory_file)

    def test_trajectory_structure(self, tmp_path):
        """Test that each trajectory has the correct structure."""
        output_dir = str(tmp_path / "generated")
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=1,
            seed=42,
            steps_per_trajectory=10,
        )
        generator.generate_dataset()

        trajectory_file = os.path.join(output_dir, "trajectory_0000.json")
        with open(trajectory_file, "r") as f:
            trajectory = json.load(f)

        assert "trajectory_id" in trajectory
        assert "hinge_count" in trajectory
        assert "material_type" in trajectory
        assert "latent_inputs" in trajectory
        assert "ground_truth_actions" in trajectory
        assert "steps_per_trajectory" in trajectory

        assert len(trajectory["latent_inputs"]) == trajectory["steps_per_trajectory"]
        assert len(trajectory["ground_truth_actions"]) == trajectory["steps_per_trajectory"]

    def test_latent_inputs_and_actions_recording(self, tmp_path):
        """Test that latent inputs and ground-truth actions are recorded for every timestep."""
        output_dir = str(tmp_path / "generated")
        steps_per_trajectory = 20
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=1,
            seed=42,
            steps_per_trajectory=steps_per_trajectory,
        )
        generator.generate_dataset()

        trajectory_file = os.path.join(output_dir, "trajectory_0000.json")
        with open(trajectory_file, "r") as f:
            trajectory = json.load(f)

        # Check that latent inputs and actions are recorded for every timestep
        assert len(trajectory["latent_inputs"]) == steps_per_trajectory
        assert len(trajectory["ground_truth_actions"]) == steps_per_trajectory

        # Check that latent inputs are lists of numbers (state vectors)
        for latent_input in trajectory["latent_inputs"]:
            assert isinstance(latent_input, list)
            assert len(latent_input) > 0
            assert all(isinstance(x, (int, float)) for x in latent_input)

        # Check that ground-truth actions are lists of numbers (action vectors)
        for action in trajectory["ground_truth_actions"]:
            assert isinstance(action, list)
            # Actions can be empty if no chain was created, but if not empty, should be numbers
            if len(action) > 0:
                assert all(isinstance(x, (int, float)) for x in action)

    def test_metadata_checksum(self, tmp_path):
        """Test that metadata contains checksums for each topology."""
        output_dir = str(tmp_path / "generated")
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=2,
            seed=42,
            steps_per_trajectory=10,
        )
        generator.generate_dataset()

        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        assert "topology_checksums" in metadata
        assert len(metadata["topology_checksums"]) == 2

        # Verify checksums are valid SHA-256 hashes
        for checksum in metadata["topology_checksums"]:
            assert len(checksum) == 64  # SHA-256 hex string length
            assert all(c in "0123456789abcdef" for c in checksum)

    def test_deterministic_generation(self, tmp_path):
        """Test that the same seed produces the same output."""
        output_dir1 = str(tmp_path / "generated1")
        output_dir2 = str(tmp_path / "generated2")

        generator1 = TopologyShiftGenerator(
            output_dir=output_dir1,
            num_topologies=2,
            seed=42,
            steps_per_trajectory=10,
        )
        generator1.generate_dataset()

        generator2 = TopologyShiftGenerator(
            output_dir=output_dir2,
            num_topologies=2,
            seed=42,
            steps_per_trajectory=10,
        )
        generator2.generate_dataset()

        # Compare metadata checksums
        with open(os.path.join(output_dir1, "metadata.json"), "r") as f1:
            metadata1 = json.load(f1)
        with open(os.path.join(output_dir2, "metadata.json"), "r") as f2:
            metadata2 = json.load(f2)

        assert metadata1["topology_checksums"] == metadata2["topology_checksums"]

    def test_zero_overlap_with_baseline(self, tmp_path, monkeypatch):
        """Test that generated topologies have zero overlap with baseline metadata."""
        # Create a fake baseline metadata file
        baseline_dir = str(tmp_path / "raw")
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_file = os.path.join(baseline_dir, "gam_baseline_metadata.json")

        baseline_data = {
            "topology_checksums": [
                compute_sha256(json.dumps({"hinge_count": 5, "material_type": "rope", "seed": 0})),
                compute_sha256(json.dumps({"hinge_count": 6, "material_type": "cloth", "seed": 1})),
            ]
        }

        with open(baseline_file, "w") as f:
            json.dump(baseline_data, f)

        # Monkeypatch the output directory to use the temp path
        output_dir = str(tmp_path / "generated")
        generator = TopologyShiftGenerator(
            output_dir=output_dir,
            num_topologies=2,
            seed=100,  # Different seed to ensure no overlap
            steps_per_trajectory=10,
        )
        generator.generate_dataset()

        # Load generated metadata
        with open(os.path.join(output_dir, "metadata.json"), "r") as f:
            generated_metadata = json.load(f)

        # Check for zero overlap
        generated_checksums = set(generated_metadata["topology_checksums"])
        baseline_checksums = set(baseline_data["topology_checksums"])

        overlap = generated_checksums.intersection(baseline_checksums)
        assert len(overlap) == 0, f"Found overlap: {overlap}"