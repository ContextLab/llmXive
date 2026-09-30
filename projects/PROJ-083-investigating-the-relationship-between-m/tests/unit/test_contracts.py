"""
Unit tests for the contract definitions (ReactionRecord and TopologicalDescriptor).
"""
import pytest
from contracts import ReactionRecord, TopologicalDescriptor, ReactionType

class TestReactionRecord:
    def test_valid_creation(self):
        """Test creating a valid ReactionRecord."""
        record = ReactionRecord(
            reaction_id="R001",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1C",
            reaction_type=ReactionType.EAS
        )
        assert record.reaction_id == "R001"
        assert record.reaction_type == ReactionType.EAS
        assert record.is_valid is True

    def test_missing_reactants_invalidates(self):
        """Test that missing reactant SMILES marks record as invalid."""
        record = ReactionRecord(
            reaction_id="R002",
            smiles_reactants="",
            smiles_products="c1ccccc1C"
        )
        assert record.is_valid is False
        assert "Missing reactant" in record.error_message

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        record = ReactionRecord(
            reaction_id="R003",
            smiles_reactants="c1ccccc1",
            smiles_products="c1ccccc1C",
            metadata={"yield": 0.85}
        )
        data = record.to_dict()
        assert data["reaction_id"] == "R003"
        assert data["metadata"]["yield"] == 0.85

    def test_from_dict_deserialization(self):
        """Test deserialization from dictionary."""
        data = {
            "reaction_id": "R004",
            "smiles_reactants": "c1ccccc1",
            "smiles_products": "c1ccccc1C",
            "reaction_type": "EAS",
            "is_valid": True
        }
        record = ReactionRecord.from_dict(data)
        assert record.reaction_id == "R004"
        assert record.reaction_type == ReactionType.EAS

    def test_empty_id_raises(self):
        """Test that empty reaction_id raises ValueError."""
        with pytest.raises(ValueError):
            ReactionRecord(
                reaction_id="",
                smiles_reactants="c1ccccc1",
                smiles_products="c1ccccc1C"
            )

class TestTopologicalDescriptor:
    def test_valid_creation(self):
        """Test creating a valid TopologicalDescriptor."""
        desc = TopologicalDescriptor(
            reaction_id="R001",
            smiles="c1ccccc1",
            molecule_role="reactant",
            wiener_index=27.0,
            balaban_index=2.0,
            zagreb_index=12.0
        )
        assert desc.reaction_id == "R001"
        assert desc.wiener_index == 27.0

    def test_disconnected_graph_flag(self):
        """Test handling of disconnected graphs."""
        desc = TopologicalDescriptor(
            reaction_id="R002",
            smiles="c1ccccc1.CC",
            molecule_role="reactant",
            is_connected=False,
            calculation_status="FAILED",
            error_message="Graph disconnected"
        )
        assert desc.is_connected is False
        assert desc.calculation_status == "FAILED"

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        desc = TopologicalDescriptor(
            reaction_id="R003",
            smiles="c1ccccc1",
            molecule_role="reactant",
            wiener_index=27.0
        )
        data = desc.to_dict()
        assert data["wiener_index"] == 27.0
        assert "reaction_id" in data

    def test_from_dict_deserialization(self):
        """Test deserialization from dictionary."""
        data = {
            "reaction_id": "R004",
            "smiles": "c1ccccc1",
            "molecule_role": "reactant",
            "wiener_index": 27.0,
            "balaban_index": 2.0
        }
        desc = TopologicalDescriptor.from_dict(data)
        assert desc.wiener_index == 27.0
        assert desc.balaban_index == 2.0

    def test_empty_smiles_raises(self):
        """Test that empty SMILES raises ValueError."""
        with pytest.raises(ValueError):
            TopologicalDescriptor(
                reaction_id="R005",
                smiles="",
                molecule_role="reactant"
            )