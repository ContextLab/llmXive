"""
Unit tests for the base schema definitions (ReactionRecord and TopologicalDescriptor).

These tests verify:
1. Data integrity (required fields, type constraints).
2. Validation logic (yield bounds, index non-negativity).
3. Immutability (frozen dataclasses).
"""
import pytest
from datetime import datetime
from contracts.schemas import ReactionRecord, TopologicalDescriptor

class TestReactionRecord:
    def test_valid_creation(self):
        """Test creation of a valid ReactionRecord."""
        record = ReactionRecord(
            reaction_id="test_001",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1O",
            smiles_reagent="O",
            reaction_type="EAS",
            yield_pct=85.5
        )
        assert record.reaction_id == "test_001"
        assert record.is_eas is True
        assert record.yield_pct == 85.5

    def test_missing_id_raises(self):
        """Test that empty reaction_id raises ValueError."""
        with pytest.raises(ValueError, match="reaction_id cannot be empty"):
            ReactionRecord(
                reaction_id="",
                smiles_reactants="c1ccccc1",
                smiles_products="c1ccccc1O",
                smiles_reagent="O",
                reaction_type="EAS"
            )

    def test_invalid_yield_raises(self):
        """Test that yield_pct outside 0-100 raises ValueError."""
        with pytest.raises(ValueError, match="yield_pct must be between 0 and 100"):
            ReactionRecord(
                reaction_id="test_002",
                smiles_reactants="c1ccccc1",
                smiles_products="c1ccccc1O",
                smiles_reagent="O",
                reaction_type="EAS",
                yield_pct=150.0
            )

    def test_missing_smiles_raises(self):
        """Test that missing SMILES raises ValueError."""
        with pytest.raises(ValueError, match="smiles_reactants cannot be empty"):
            ReactionRecord(
                reaction_id="test_003",
                smiles_reactants="",
                smiles_products="c1ccccc1O",
                smiles_reagent="O",
                reaction_type="EAS"
            )

    def test_is_eas_case_insensitive(self):
        """Test that is_eas property handles case variations."""
        record_lower = ReactionRecord(
            reaction_id="test_004",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1O",
            smiles_reagent="O",
            reaction_type="eas"
        )
        record_upper = ReactionRecord(
            reaction_id="test_005",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1O",
            smiles_reagent="O",
            reaction_type="EAS"
        )
        assert record_lower.is_eas is True
        assert record_upper.is_eas is True

    def test_immutability(self):
        """Test that ReactionRecord is frozen (immutable)."""
        record = ReactionRecord(
            reaction_id="test_006",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1O",
            smiles_reagent="O",
            reaction_type="EAS"
        )
        with pytest.raises(Exception): # Frozen dataclass raises FrozenInstanceError
            record.reaction_id = "new_id"

class TestTopologicalDescriptor:
    def test_valid_creation(self):
        """Test creation of a valid TopologicalDescriptor."""
        desc = TopologicalDescriptor(
            reaction_id="test_001",
            smiles="c1ccccc1",
            wiener_index=27.0,
            balaban_index=1.5,
            zagreb_index=12.0,
            atom_count=6,
            bond_count=6,
            is_valid_topology=True
        )
        assert desc.reaction_id == "test_001"
        assert desc.wiener_index == 27.0
        assert desc.feature_vector == [27.0, 1.5, 12.0]

    def test_invalid_atom_count_raises(self):
        """Test that non-positive atom_count raises ValueError."""
        with pytest.raises(ValueError, match="atom_count must be positive"):
            TopologicalDescriptor(
                reaction_id="test_001",
                smiles="c1ccccc1",
                wiener_index=27.0,
                balaban_index=1.5,
                zagreb_index=12.0,
                atom_count=0,
                bond_count=6,
                is_valid_topology=True
            )

    def test_invalid_bond_count_raises(self):
        """Test that negative bond_count raises ValueError."""
        with pytest.raises(ValueError, match="bond_count cannot be negative"):
            TopologicalDescriptor(
                reaction_id="test_001",
                smiles="c1ccccc1",
                wiener_index=27.0,
                balaban_index=1.5,
                zagreb_index=12.0,
                atom_count=6,
                bond_count=-1,
                is_valid_topology=True
            )

    def test_negative_index_on_valid_topology_raises(self):
        """Test that negative indices on valid topology raise ValueError."""
        with pytest.raises(ValueError, match="Topological indices must be non-negative"):
            TopologicalDescriptor(
                reaction_id="test_001",
                smiles="c1ccccc1",
                wiener_index=-1.0,
                balaban_index=1.5,
                zagreb_index=12.0,
                atom_count=6,
                bond_count=6,
                is_valid_topology=True
            )

    def test_invalid_topology_allows_negative_indices(self):
        """Test that invalid topology does not strictly enforce non-negative indices (as they might be NaN/0)."""
        # This should not raise, as the graph was invalid
        desc = TopologicalDescriptor(
            reaction_id="test_001",
            smiles="invalid_smiles",
            wiener_index=-1.0,
            balaban_index=-1.0,
            zagreb_index=-1.0,
            atom_count=0,
            bond_count=0,
            is_valid_topology=False
        )
        assert desc.is_valid_topology is False

    def test_to_dict(self):
        """Test dictionary serialization."""
        desc = TopologicalDescriptor(
            reaction_id="test_001",
            smiles="c1ccccc1",
            wiener_index=27.0,
            balaban_index=1.5,
            zagreb_index=12.0,
            atom_count=6,
            bond_count=6,
            is_valid_topology=True,
            symmetry_class=1
        )
        data = desc.to_dict()
        assert data["reaction_id"] == "test_001"
        assert data["wiener_index"] == 27.0
        assert data["symmetry_class"] == 1
        assert "calculation_timestamp" in data