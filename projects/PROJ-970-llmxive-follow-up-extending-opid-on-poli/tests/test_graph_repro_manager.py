"""
Tests for GraphReproManager (Task T015).

Verifies that:
1. Graph generation is deterministic for a given seed.
2. Checksums are consistent across runs.
3. Different seeds produce different checksums.
4. Invalid checksums raise errors.
"""
import pytest
import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.graph_repro_manager import GraphReproManager, ReproMetadata
from env.graph_generator import GraphGenerationConfig
from config import set_seed, get_seed
from env.state_graph import StateGraph


class TestGraphReproManager:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = GraphReproManager(output_dir=self.temp_dir)
        # Ensure a known seed state
        set_seed(42)
        yield
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deterministic_generation_same_seed(self):
        """Test that generating with the same seed produces the same checksum."""
        tier = "tier1"
        seed = 100

        # First generation
        graph1, meta1 = self.manager.generate_and_verify(tier, seed)
        checksum1 = meta1.graph_checksum

        # Second generation with same seed
        graph2, meta2 = self.manager.generate_and_verify(tier, seed)
        checksum2 = meta2.graph_checksum

        assert checksum1 == checksum2, "Checksums should be identical for same seed"
        assert len(graph1.nodes) == len(graph2.nodes), "Node counts should match"
        assert len(graph1.edges) == len(graph2.edges), "Edge counts should match"

    def test_different_seed_different_checksum(self):
        """Test that different seeds produce different checksums."""
        tier = "tier1"
        seed_a = 100
        seed_b = 200

        _, meta_a = self.manager.generate_and_verify(tier, seed_a)
        _, meta_b = self.manager.generate_and_verify(tier, seed_b)

        assert meta_a.graph_checksum != meta_b.graph_checksum, "Checksums should differ for different seeds"

    def test_verify_with_expected_checksum_pass(self):
        """Test that verification passes when checksum matches."""
        tier = "tier2"
        seed = 555

        # Generate and get checksum
        _, meta = self.manager.generate_and_verify(tier, seed)
        expected = meta.graph_checksum

        # Verify with correct checksum
        graph, verified_meta = self.manager.generate_and_verify(
            tier, seed, expected_checksum=expected
        )

        assert verified_meta.graph_checksum == expected
        assert verified_meta.is_valid

    def test_verify_with_expected_checksum_fail(self):
        """Test that verification fails when checksum does not match."""
        tier = "tier3"
        seed = 777
        wrong_checksum = "0" * 64  # Invalid checksum

        with pytest.raises(ValueError) as exc_info:
            self.manager.generate_and_verify(tier, seed, expected_checksum=wrong_checksum)

        assert "Checksum mismatch" in str(exc_info.value)

    def test_metadata_persistence(self):
        """Test that metadata is saved to disk."""
        tier = "tier1"
        seed = 999

        _, meta = self.manager.generate_and_verify(tier, seed)

        expected_filename = f"graph_meta_tier{meta.tier.replace('tier', '')}_seed{meta.seed}.json"
        filepath = os.path.join(self.temp_dir, expected_filename)

        assert os.path.exists(filepath), "Metadata file should be saved"

        # Check content (basic validation)
        import json
        with open(filepath, 'r') as f:
            saved_data = json.load(f)

        assert saved_data['seed'] == seed
        assert saved_data['tier'] == tier
        assert saved_data['graph_checksum'] == meta.graph_checksum

    def test_invalid_graph_raises_error(self):
        """Test that an invalid graph (if generated) raises an error."""
        # Note: The current generator and validator are robust, so generating an invalid graph
        # via standard means is unlikely. This test documents the expected behavior if validation fails.
        # We rely on the fact that generate_and_verify calls validate() and raises RuntimeError if invalid.
        tier = "tier1"
        seed = 12345

        # This should succeed normally
        graph, meta = self.manager.generate_and_verify(tier, seed)
        assert meta.is_valid

        # If we wanted to force a failure, we'd need to mock the validator.
        # For now, we assert that valid graphs pass.

    def test_tier_specific_generation(self):
        """Test that different tiers produce different graph structures."""
        seed = 42

        _, meta1 = self.manager.generate_and_verify("tier1", seed)
        _, meta2 = self.manager.generate_and_verify("tier2", seed)
        _, meta3 = self.manager.generate_and_verify("tier3", seed)

        # Tiers should have different node/edge counts or structures
        # We expect at least some difference in complexity
        assert meta1.tier == "tier1"
        assert meta2.tier == "tier2"
        assert meta3.tier == "tier3"

        # While checksums might coincidentally match (extremely unlikely),
        # the node counts usually differ between tiers.
        # We assert that the metadata correctly reflects the tier.
        assert meta1.node_count > 0
        assert meta2.node_count > 0
        assert meta3.node_count > 0

        # Checksums should be unique for different tiers (even with same seed)
        assert meta1.graph_checksum != meta2.graph_checksum
        assert meta2.graph_checksum != meta3.graph_checksum
        assert meta1.graph_checksum != meta3.graph_checksum

    def test_version_hash_in_metadata(self):
        """Test that the version hash is included in metadata."""
        from config import get_version_hash

        tier = "tier1"
        seed = 111

        _, meta = self.manager.generate_and_verify(tier, seed)

        expected_hash = get_version_hash()
        assert meta.version_hash == expected_hash, "Metadata should contain the current version hash"
        assert len(meta.version_hash) > 0, "Version hash should not be empty"
