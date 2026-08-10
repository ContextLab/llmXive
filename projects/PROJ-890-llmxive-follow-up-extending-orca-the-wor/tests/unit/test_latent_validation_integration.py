"""
Integration test for T017: Verify output shape and validity of latent vectors.

This test runs the validation logic end-to-end by:
1. Checking that extract_latents.py produced valid output
2. Running all validation checks from test_latent_validation.py
3. Reporting detailed failure information
"""

import os
import sys
import csv
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_config


class TestLatentValidationIntegration:
    """Integration test for latent vector validation pipeline."""

    @pytest.fixture
    def config(self):
        return get_config()

    @pytest.fixture
    def latents_path(self, config):
        return config["DATA_PROCESSED_DIR"] / "latents.csv"

    def test_full_validation_pipeline(self, latents_path, config):
        """
        Run the complete validation pipeline on the extracted latents.
        
        This simulates what a CI/CD pipeline would do:
        1. Verify file exists
        2. Load data
        3. Run all shape and validity checks
        4. Report results
        """
        if not latents_path.exists():
            pytest.skip("Latents CSV not found. Run extract_latents.py first.")

        # Load data
        latents = []
        with open(latents_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vector_str = row["latent_vector"].strip("[]")
                vector_values = [float(x.strip()) for x in vector_str.split(",") if x.strip()]
                latents.append({
                    "video_id": row["video_id"],
                    "prompt": row["prompt"],
                    "vector": np.array(vector_values, dtype=np.float32)
                })

        assert len(latents) > 0, "No latents found in CSV"

        # Validation checks
        expected_dim = config.get("EXPECTED_LATENT_DIM", 768)
        errors = []

        for item in latents:
            # Check shape
            if item["vector"].shape != (expected_dim,):
                errors.append(f"{item['video_id']}: Shape mismatch {item['vector'].shape} vs ({expected_dim},)")

            # Check dtype
            if not np.issubdtype(item["vector"].dtype, np.floating):
                errors.append(f"{item['video_id']}: Invalid dtype {item['vector'].dtype}")

            # Check NaN
            if np.isnan(item["vector"]).any():
                errors.append(f"{item['video_id']}: Contains NaN")

            # Check Inf
            if np.isinf(item["vector"]).any():
                errors.append(f"{item['video_id']}: Contains Inf")

            # Check range
            if item["vector"].min() < -10.0 or item["vector"].max() > 10.0:
                errors.append(
                    f"{item['video_id']}: Out of range [{item['vector'].min():.2f}, {item['vector'].max():.2f}]"
                )

        if errors:
            pytest.fail("Validation failed with errors:\n" + "\n".join(errors))

        # If we get here, all checks passed
        assert True, f"All {len(latents)} latent vectors passed validation"

    def test_statistics_summary(self, latents_path):
        """Generate and verify basic statistics about the extracted latents."""
        if not latents_path.exists():
            pytest.skip("Latents CSV not found.")

        vectors = []
        with open(latents_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vector_str = row["latent_vector"].strip("[]")
                vector_values = [float(x.strip()) for x in vector_str.split(",") if x.strip()]
                vectors.append(np.array(vector_values))

        if not vectors:
            pytest.skip("No vectors to analyze")

        all_vectors = np.vstack(vectors)
        
        # Verify we can compute basic statistics without error
        stats = {
            "mean": np.mean(all_vectors),
            "std": np.std(all_vectors),
            "min": np.min(all_vectors),
            "max": np.max(all_vectors),
            "count": len(vectors)
        }

        # Sanity checks on statistics
        assert not np.isnan(stats["mean"]), "Mean is NaN"
        assert not np.isinf(stats["mean"]), "Mean is Inf"
        assert stats["count"] > 0, "Count is zero"

        # Log for debugging
        print(f"Latent Statistics: {stats}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])