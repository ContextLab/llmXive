import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.evomem_all import EvoMemAll
from src.agents.evomem_conflict import EvoMemConflict
from src.heuristics.conflict_detector import ConflictDetector
from src.data.generators.synthetic_pairs import generate_synthetic_pairs, read_sample_size_from_research_md
from src.utils.logging import get_logger
from src.utils.seeding import set_deterministic_seed

# Set deterministic seed for reproducibility
set_deterministic_seed(42)

# Constants for test
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "integration_tests"
TEST_SYNTHETIC_PAIRS_PATH = TEST_OUTPUT_DIR / "synthetic_pairs_test.json"
TEST_LOG_PATH = TEST_OUTPUT_DIR / "agent_filtering_test.log"

# Ensure test output directory exists
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class TestEvoMemConflictFiltering:
    """
    Integration test for T018: Verify that EvoMem-Conflict correctly filters
    non-conflict patches using the heuristic from US1.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment: generate synthetic pairs and initialize agents."""
        # Generate a small set of synthetic pairs for testing
        # We force a specific count to ensure we have both conflict and non-conflict cases
        self.test_count = 20
        self.conflict_ratio = 0.5  # 50% contradiction, 50% non-contradiction

        # Generate synthetic pairs
        pairs = []
        base_patches = []
        
        # Create base patches
        for i in range(self.test_count):
            base_patch = f"State update {i}: User {i} has balance {1000 + i}."
            base_patches.append(base_patch)
        
        # Generate contradiction and non-contradiction pairs
        for i in range(self.test_count):
            if i % 2 == 0:
                # Contradiction: change the balance
                patch_b = f"State update {i}: User {i} has balance {500 + i}." # Changed balance
                is_contradiction = True
            else:
                # Non-contradiction: add unrelated info
                patch_b = f"State update {i}: User {i} has balance {1000 + i}. Last login: 2023-01-{i+1:02d}."
                is_contradiction = False
            
            pairs.append({
                "patch_a": base_patches[i],
                "patch_b": patch_b,
                "is_contradiction": is_contradiction
            })

        # Write to file
        with open(self.TEST_SYNTHETIC_PAIRS_PATH, 'w') as f:
            json.dump(pairs, f, indent=2)

        # Initialize agents
        # EvoMemAll: retrieves all patches (baseline)
        self.agent_all = EvoMemAll(
            max_patches=self.test_count,
            logger=get_logger("test_evo_all", TEST_OUTPUT_DIR)
        )

        # EvoMemConflict: retrieves only conflicting patches + fallback
        # We pass the path to our synthetic pairs as the "memory" source
        self.agent_conflict = EvoMemConflict(
            max_patches=self.test_count,
            logger=get_logger("test_evo_conflict", TEST_OUTPUT_DIR),
            memory_source_path=self.TEST_SYNTHETIC_PAIRS_PATH
        )

        # Initialize conflict detector
        self.detector = ConflictDetector(
            model_name="distilbert-base-uncased",
            threshold=0.90,
            logger=get_logger("test_detector", TEST_OUTPUT_DIR)
        )

    def test_conflict_detector_flags_correctly(self):
        """Verify the conflict detector identifies contradictions in our synthetic data."""
        results = []
        with open(self.TEST_SYNTHETIC_PAIRS_PATH, 'r') as f:
            data = json.load(f)
        
        for item in data:
            score, is_conflict = self.detector.detect(item['patch_a'], item['patch_b'])
            results.append({
                "is_contradiction": item['is_contradiction'],
                "predicted_conflict": is_conflict,
                "score": score
            })
        
        # Check that we have at least some detections
        detected_count = sum(1 for r in results if r['predicted_conflict'])
        assert detected_count > 0, "Detector should flag at least some conflicts"

    def test_evomem_conflict_filters_non_conflicts(self):
        """
        Main test for T018: Verify that EvoMem-Conflict retrieves significantly
        fewer patches than EvoMem-All when non-conflict patches exist.
        """
        # Simulate retrieval for both agents
        # We pass the synthetic pairs as the "task context" to retrieve from
        with open(self.TEST_SYNTHETIC_PAIRS_PATH, 'r') as f:
            test_data = json.load(f)
        
        # EvoMemAll retrieves all patches (up to max_patches)
        retrieved_all = self.agent_all.retrieve_patches(test_data)
        
        # EvoMemConflict retrieves only conflicting patches (plus fallback if needed)
        retrieved_conflict = self.agent_conflict.retrieve_patches(test_data)
        
        # Log results
        logger = get_logger("test_evo_conflict_filtering", TEST_OUTPUT_DIR)
        logger.info(f"Total patches in dataset: {len(test_data)}")
        logger.info(f"EvoMem-All retrieved: {len(retrieved_all)} patches")
        logger.info(f"EvoMem-Conflict retrieved: {len(retrieved_conflict)} patches")
        
        # Assertion 1: EvoMem-Conflict should retrieve <= EvoMem-All
        assert len(retrieved_conflict) <= len(retrieved_all), \
            "EvoMem-Conflict should not retrieve more patches than EvoMem-All"
        
        # Assertion 2: If we have non-conflict patches, EvoMem-Conflict should retrieve fewer
        # (unless all are conflicts, which is unlikely with 50/50 ratio)
        actual_conflicts = sum(1 for item in test_data if item['is_contradiction'])
        actual_non_conflicts = len(test_data) - actual_conflicts
        
        logger.info(f"Actual conflicts in dataset: {actual_conflicts}")
        logger.info(f"Actual non-conflicts in dataset: {actual_non_conflicts}")
        
        # If there are non-conflict patches, the conflict agent should filter them out
        if actual_non_conflicts > 0:
            # The conflict agent should retrieve at most (conflicts + fallback)
            # Fallback is latest state + 2 most recent non-conflicts
            max_expected = actual_conflicts + 3  # +3 for fallback logic
            
            # Allow some tolerance for the fallback logic
            assert len(retrieved_conflict) <= max_expected, \
                f"EvoMem-Conflict retrieved {len(retrieved_conflict)} patches, expected <= {max_expected}"
            
            # Most importantly, it should be strictly less than all if we have non-conflicts
            # and the detector is working
            if actual_conflicts < len(test_data):
                assert len(retrieved_conflict) < len(retrieved_all), \
                    "EvoMem-Conflict should filter out non-conflict patches"

    def test_fallback_logic_on_empty_conflicts(self):
        """
        Test that EvoMem-Conflict falls back to latest state + 2 non-conflicts
        when no conflicts are detected (simulating detector failure or no conflicts).
        """
        # Create a dataset with NO contradictions
        no_conflict_data = []
        for i in range(10):
            no_conflict_data.append({
                "patch_a": f"State {i}: User {i} has balance {1000+i}.",
                "patch_b": f"State {i}: User {i} has balance {1000+i}. Updated profile.",
                "is_contradiction": False
            })
        
        # Write to temp file
        temp_path = TEST_OUTPUT_DIR / "no_conflict_test.json"
        with open(temp_path, 'w') as f:
            json.dump(no_conflict_data, f)
        
        # Create agent with this data
        agent = EvoMemConflict(
            max_patches=10,
            logger=get_logger("test_fallback", TEST_OUTPUT_DIR),
            memory_source_path=temp_path
        )
        
        # Retrieve
        retrieved = agent.retrieve_patches(no_conflict_data)
        
        # Fallback should retrieve latest state + 2 most recent non-conflicts
        # So we expect at least 3 patches (1 latest + 2 non-conflicts)
        assert len(retrieved) >= 3, \
            f"Fallback should retrieve at least 3 patches (latest + 2 non-conflicts), got {len(retrieved)}"
        
        logger = get_logger("test_fallback", TEST_OUTPUT_DIR)
        logger.info(f"Fallback retrieved {len(retrieved)} patches when no conflicts detected")

    def test_context_reduction_ratio(self):
        """
        Calculate and verify the context reduction ratio achieved by filtering.
        This quantifies the efficiency gain of EvoMem-Conflict.
        """
        with open(self.TEST_SYNTHETIC_PAIRS_PATH, 'r') as f:
            test_data = json.load(f)
        
        retrieved_all = self.agent_all.retrieve_patches(test_data)
        retrieved_conflict = self.agent_conflict.retrieve_patches(test_data)
        
        if len(retrieved_all) == 0:
            pytest.skip("No patches retrieved by EvoMem-All, cannot calculate ratio")
        
        reduction_ratio = 1.0 - (len(retrieved_conflict) / len(retrieved_all))
        
        logger = get_logger("test_reduction", TEST_OUTPUT_DIR)
        logger.info(f"Context reduction ratio: {reduction_ratio:.2%}")
        logger.info(f"Patches filtered out: {len(retrieved_all) - len(retrieved_conflict)}")
        
        # We expect a positive reduction if there are non-conflict patches
        actual_non_conflicts = sum(1 for item in test_data if not item['is_contradiction'])
        if actual_non_conflicts > 0:
            assert reduction_ratio > 0, \
                "Expected positive reduction ratio when non-conflict patches exist"

    def test_output_format_correctness(self):
        """
        Verify that retrieved patches have the correct structure for downstream consumption.
        """
        with open(self.TEST_SYNTHETIC_PAIRS_PATH, 'r') as f:
            test_data = json.load(f)
        
        retrieved = self.agent_conflict.retrieve_patches(test_data)
        
        for patch in retrieved:
            assert "patch_a" in patch, "Retrieved patch must contain patch_a"
            assert "patch_b" in patch, "Retrieved patch must contain patch_b"
            assert "is_contradiction" in patch or "predicted_conflict" in patch, \
                "Retrieved patch must contain conflict status"
        
        logger = get_logger("test_format", TEST_OUTPUT_DIR)
        logger.info(f"Verified {len(retrieved)} patches have correct structure")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
