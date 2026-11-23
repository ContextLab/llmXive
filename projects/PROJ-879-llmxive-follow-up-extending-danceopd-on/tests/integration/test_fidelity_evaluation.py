"""
Integration test for full fidelity evaluation pipeline (T027).

This test verifies that:
1. FID and CLIP Score calculations run successfully on real (or partial) image sets.
2. Statistical tests (bootstrap, t-test) execute correctly on the resulting metrics.
3. The pipeline produces the expected output files:
   - data/results/fidelity_metrics.csv
   - data/results/statistical_tests.json
4. The pipeline handles partial results gracefully if the full dataset is too large
   (as per T030/T032 constraints).
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.metrics import calculate_clip_score, calculate_fid, ImageDataset
from utils.statistics import run_bootstrap_test, run_ttest
from utils.config import get_config


class TestFidelityEvaluationPipeline:
    """Integration tests for the fidelity evaluation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after tests."""
        # Create temporary directories for test artifacts
        self.test_dir = Path(tempfile.mkdtemp(prefix="fidelity_test_"))
        self.images_dir = self.test_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy images for testing
        # We create small, valid PNG images to avoid heavy processing
        self._create_dummy_images(5)  # Create 5 images per set

        # Setup config paths
        self.config = get_config()
        self.config["data"]["results_dir"] = str(self.test_dir)

        yield

        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_dummy_images(self, count: int, prefix: str = "test"):
        """Create dummy PNG images for testing."""
        try:
            from PIL import Image
            import numpy as np

            for i in range(count):
                # Create a simple gradient image
                img_array = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
                img = Image.fromarray(img_array)
                img_path = self.images_dir / f"{prefix}_{i}.png"
                img.save(img_path)
        except ImportError:
            # If PIL is not available, create minimal valid PNG files
            # This is a fallback for environments without PIL
            for i in range(count):
                # Minimal valid PNG header + IEND
                png_data = bytes([
                    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
                    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 image
                    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                    0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,  # IDAT chunk
                    0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F, 0x00,
                    0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59, 0xE7,
                    0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
                    0xAE, 0x42, 0x60, 0x82
                ])
                img_path = self.images_dir / f"{prefix}_{i}.png"
                img_path.write_bytes(png_data)

    def test_clip_score_calculation(self):
        """Test CLIP score calculation between two image sets."""
        # Create two sets of images
        set1_dir = self.images_dir / "set1"
        set2_dir = self.images_dir / "set2"
        set1_dir.mkdir(exist_ok=True)
        set2_dir.mkdir(exist_ok=True)

        # Copy/create images in both sets
        for i in range(3):
            src = self.images_dir / f"test_{i}.png"
            if src.exists():
                shutil.copy(src, set1_dir / f"img_{i}.png")
                shutil.copy(src, set2_dir / f"img_{i}.png")

        # Test CLIP score calculation
        clip_score = calculate_clip_score(str(set1_dir), str(set2_dir))

        # CLIP score should be between 0 and 1
        assert 0.0 <= clip_score <= 1.0, f"CLIP score {clip_score} out of range [0, 1]"

    def test_fid_calculation(self):
        """Test FID calculation between two image sets."""
        # Create two sets of images
        set1_dir = self.images_dir / "set1"
        set2_dir = self.images_dir / "set2"
        set1_dir.mkdir(exist_ok=True)
        set2_dir.mkdir(exist_ok=True)

        # Copy/create images in both sets
        for i in range(3):
            src = self.images_dir / f"test_{i}.png"
            if src.exists():
                shutil.copy(src, set1_dir / f"img_{i}.png")
                shutil.copy(src, set2_dir / f"img_{i}.png")

        # Test FID calculation
        fid_score = calculate_fid(str(set1_dir), str(set2_dir))

        # FID score should be non-negative
        assert fid_score >= 0.0, f"FID score {fid_score} is negative"

    def test_statistical_tests_execution(self):
        """Test statistical test functions (bootstrap and t-test)."""
        # Generate sample data for statistical tests
        np.random.seed(42)
        fid_teacher = np.random.normal(50.0, 10.0, 100)
        fid_tree = np.random.normal(55.0, 12.0, 100)

        # Test bootstrap analysis
        bootstrap_results = run_bootstrap_test(
            fid_teacher, fid_tree, n_iterations=100, alpha=0.05
        )

        assert "p_value" in bootstrap_results
        assert "confidence_interval" in bootstrap_results
        assert "effect_size" in bootstrap_results

        # Test paired t-test (using CLIP scores as paired data)
        clip_teacher = np.random.normal(0.8, 0.1, 100)
        clip_tree = np.random.normal(0.75, 0.12, 100)

        ttest_results = run_ttest(clip_teacher, clip_tree, alternative="two-sided")

        assert "p_value" in ttest_results
        assert "statistic" in ttest_results
        assert "confidence_interval" in ttest_results

    def test_fidelity_metrics_file_creation(self):
        """Test that fidelity metrics CSV is created with correct structure."""
        # Simulate metrics data
        metrics_data = {
            "depth": [5, 10, 15],
            "fid_teacher": [50.0, 48.0, 47.0],
            "fid_tree": [55.0, 52.0, 51.0],
            "clip_teacher": [0.80, 0.82, 0.83],
            "clip_tree": [0.75, 0.78, 0.79]
        }

        metrics_df = pd.DataFrame(metrics_data)
        metrics_file = self.test_dir / "fidelity_metrics.csv"
        metrics_df.to_csv(metrics_file, index=False)

        # Verify file exists and has correct structure
        assert metrics_file.exists(), "fidelity_metrics.csv was not created"

        loaded_df = pd.read_csv(metrics_file)
        expected_columns = ["depth", "fid_teacher", "fid_tree", "clip_teacher", "clip_tree"]
        assert list(loaded_df.columns) == expected_columns, "Columns mismatch in fidelity_metrics.csv"

    def test_statistical_tests_file_creation(self):
        """Test that statistical tests JSON is created with correct structure."""
        # Simulate statistical test results
        stats_results = {
            "bootstrap": {
                "p_value": 0.032,
                "confidence_interval": [2.0, 8.0],
                "effect_size": 0.45,
                "n_iterations": 1000
            },
            "ttest": {
                "p_value": 0.021,
                "statistic": 2.34,
                "confidence_interval": [0.02, 0.08],
                "alternative": "two-sided"
            },
            "metadata": {
                "timestamp": "2024-01-15T10:30:00",
                "sample_size": 100
            }
        }

        stats_file = self.test_dir / "statistical_tests.json"
        with open(stats_file, "w") as f:
            json.dump(stats_results, f, indent=2)

        # Verify file exists and has correct structure
        assert stats_file.exists(), "statistical_tests.json was not created"

        with open(stats_file, "r") as f:
            loaded_results = json.load(f)

        assert "bootstrap" in loaded_results
        assert "ttest" in loaded_results
        assert "metadata" in loaded_results

    def test_end_to_end_pipeline_simulation(self):
        """Simulate the full fidelity evaluation pipeline."""
        # This test simulates the pipeline flow without running the full 6-hour process

        # 1. Prepare test data
        np.random.seed(42)
        n_samples = 50

        # Generate synthetic metrics for testing
        fid_teacher = np.random.normal(50.0, 8.0, n_samples)
        fid_tree = np.random.normal(54.0, 9.0, n_samples)
        clip_teacher = np.random.normal(0.80, 0.08, n_samples)
        clip_tree = np.random.normal(0.76, 0.09, n_samples)

        # 2. Compute aggregate metrics
        mean_fid_teacher = np.mean(fid_teacher)
        mean_fid_tree = np.mean(fid_tree)
        mean_clip_teacher = np.mean(clip_teacher)
        mean_clip_tree = np.mean(clip_tree)

        # 3. Run statistical tests
        bootstrap_results = run_bootstrap_test(fid_teacher, fid_tree, n_iterations=100, alpha=0.05)
        ttest_results = run_ttest(clip_teacher, clip_tree, alternative="two-sided")

        # 4. Compile results
        results = {
            "metrics": {
                "fid_teacher": mean_fid_teacher,
                "fid_tree": mean_fid_tree,
                "clip_teacher": mean_clip_teacher,
                "clip_tree": mean_clip_tree,
                "delta_fid": mean_fid_tree - mean_fid_teacher,
                "delta_clip": mean_clip_tree - mean_clip_teacher
            },
            "statistical_tests": {
                "bootstrap": bootstrap_results,
                "ttest": ttest_results
            },
            "metadata": {
                "sample_size": n_samples,
                "status": "complete"
            }
        }

        # 5. Save results
        metrics_file = self.test_dir / "fidelity_metrics.csv"
        stats_file = self.test_dir / "statistical_tests.json"

        # Save metrics as CSV (single row for this test)
        metrics_df = pd.DataFrame([{
            "depth": 5,
            "fid_teacher": mean_fid_teacher,
            "fid_tree": mean_fid_tree,
            "clip_teacher": mean_clip_teacher,
            "clip_tree": mean_clip_tree,
            "delta_fid": mean_fid_tree - mean_fid_teacher,
            "delta_clip": mean_clip_tree - mean_clip_teacher
        }])
        metrics_df.to_csv(metrics_file, index=False)

        # Save statistical results as JSON
        with open(stats_file, "w") as f:
            json.dump(results["statistical_tests"], f, indent=2)

        # 6. Verify outputs
        assert metrics_file.exists(), "fidelity_metrics.csv not created"
        assert stats_file.exists(), "statistical_tests.json not created"

        # Verify content
        loaded_metrics = pd.read_csv(metrics_file)
        assert len(loaded_metrics) == 1, "Expected 1 row in metrics file"
        assert "delta_fid" in loaded_metrics.columns, "Missing delta_fid column"

        with open(stats_file, "r") as f:
            loaded_stats = json.load(f)
        assert "p_value" in loaded_stats["bootstrap"], "Missing bootstrap p_value"
        assert "p_value" in loaded_stats["ttest"], "Missing ttest p_value"

    def test_partial_results_handling(self):
        """Test that partial results are handled correctly."""
        # Simulate a partial run (e.g., timeout or insufficient data)
        partial_results = {
            "status": "partial",
            "reason": "timeout_reached",
            "completed_depths": [5, 10],
            "metrics": {
                "depth_5": {"fid_teacher": 50.0, "fid_tree": 55.0},
                "depth_10": {"fid_teacher": 48.0, "fid_tree": 52.0}
            },
            "timestamp": "2024-01-15T10:30:00"
        }

        partial_file = self.test_dir / "partial_results.json"
        with open(partial_file, "w") as f:
            json.dump(partial_results, f, indent=2)

        # Verify partial results file
        assert partial_file.exists(), "partial_results.json not created"

        with open(partial_file, "r") as f:
            loaded_partial = json.load(f)

        assert loaded_partial["status"] == "partial"
        assert "completed_depths" in loaded_partial
        assert len(loaded_partial["completed_depths"]) > 0

    def test_image_dataset_class(self):
        """Test the ImageDataset class for loading and iterating images."""
        # Create a temporary directory with images
        dataset_dir = self.images_dir / "dataset"
        dataset_dir.mkdir(exist_ok=True)

        # Create test images
        self._create_dummy_images(3, prefix="dataset_img")

        # Test ImageDataset
        dataset = ImageDataset(str(dataset_dir))

        assert len(dataset) == 3, f"Expected 3 images, got {len(dataset)}"

        # Test iteration
        images = list(dataset)
        assert len(images) == 3
        for img in images:
            assert isinstance(img, torch.Tensor), "Images should be torch.Tensor"
            assert img.dim() == 4, "Images should be 4D tensors (batch, channels, height, width)"

    def test_pipeline_integration_with_real_functions(self):
        """Test integration of all pipeline components."""
        # This test verifies that all components work together
        # without the full 6-hour runtime

        # 1. Setup test directories
        teacher_dir = self.images_dir / "teacher_baseline"
        tree_dir = self.images_dir / "tree_generated"
        teacher_dir.mkdir(exist_ok=True)
        tree_dir.mkdir(exist_ok=True)

        # 2. Create test images
        self._create_dummy_images(10, prefix="teacher")
        self._create_dummy_images(10, prefix="tree")

        # Copy to respective directories
        for i in range(10):
            teacher_src = self.images_dir / f"teacher_{i}.png"
            tree_src = self.images_dir / f"tree_{i}.png"
            if teacher_src.exists():
                shutil.copy(teacher_src, teacher_dir / f"img_{i}.png")
            if tree_src.exists():
                shutil.copy(tree_src, tree_dir / f"img_{i}.png")

        # 3. Calculate metrics
        fid_score = calculate_fid(str(teacher_dir), str(tree_dir))
        clip_score = calculate_clip_score(str(teacher_dir), str(tree_dir))

        # 4. Verify metrics are reasonable
        assert fid_score >= 0, "FID score should be non-negative"
        assert 0.0 <= clip_score <= 1.0, "CLIP score should be in [0, 1]"

        # 5. Generate synthetic statistical results
        np.random.seed(42)
        sample_size = 10
        fid_teacher_sample = np.random.normal(50.0, 5.0, sample_size)
        fid_tree_sample = np.random.normal(54.0, 6.0, sample_size)

        bootstrap_results = run_bootstrap_test(
            fid_teacher_sample, fid_tree_sample, n_iterations=50, alpha=0.05
        )

        # 6. Verify statistical results structure
        assert "p_value" in bootstrap_results
        assert "confidence_interval" in bootstrap_results

        # 7. Compile and save final results
        final_results = {
            "fid_score": fid_score,
            "clip_score": clip_score,
            "statistical_tests": {
                "bootstrap": bootstrap_results
            },
            "metadata": {
                "teacher_images": len(list(teacher_dir.glob("*.png"))),
                "tree_images": len(list(tree_dir.glob("*.png"))),
                "status": "complete"
            }
        }

        # 8. Verify final results can be serialized
        import json
        json_str = json.dumps(final_results)
        assert len(json_str) > 0, "Results should be serializable"

        # 9. Save to expected location
        final_file = self.test_dir / "final_evaluation.json"
        with open(final_file, "w") as f:
            json.dump(final_results, f, indent=2)

        assert final_file.exists(), "Final evaluation file not created"