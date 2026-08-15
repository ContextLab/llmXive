import pytest
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingest import detect_water_mediated_interactions
from models.entities import Atom

def create_atom(atom_type: str, coords: list) -> Atom:
    """Helper to create an Atom object for testing."""
    return Atom(
        atom_type=atom_type,
        coords=np.array(coords, dtype=np.float32),
        charge=0.0,
        hydrophobicity=0.0
    )

class TestWaterMediatedInteractions:
    
    def test_no_water(self):
        """Test detection when no water atoms are present."""
        protein = [create_atom("C", [0, 0, 0])]
        ligand = [create_atom("O", [4, 0, 0])]
        water = []
        
        has_bridge, bridges = detect_water_mediated_interactions(protein, ligand, water)
        assert has_bridge is False
        assert bridges == []

    def test_water_too_far(self):
        """Test detection when water is too far from both protein and ligand."""
        protein = [create_atom("C", [0, 0, 0])]
        ligand = [create_atom("O", [4, 0, 0])]
        # Water at [10, 10, 10] - far from both
        water = [create_atom("O", [10, 10, 10])]
        
        has_bridge, bridges = detect_water_mediated_interactions(protein, ligand, water)
        assert has_bridge is False
        assert bridges == []

    def test_water_bridge_detected(self):
        """Test detection of a valid water bridge."""
        # Protein at (0,0,0), Ligand at (4,0,0)
        # Water at (2, 1, 0) -> dist to protein = sqrt(5) ~ 2.24, dist to ligand = sqrt(5) ~ 2.24
        # Both < 3.5 threshold
        protein = [create_atom("C", [0, 0, 0])]
        ligand = [create_atom("O", [4, 0, 0])]
        water = [create_atom("O", [2, 1, 0])]
        
        has_bridge, bridges = detect_water_mediated_interactions(protein, ligand, water)
        assert has_bridge is True
        assert len(bridges) == 1
        # Check indices: protein_idx=0, water_idx=0, ligand_idx=0
        assert bridges[0] == (0, 0, 0)

    def test_multiple_waters(self):
        """Test detection with multiple water molecules."""
        protein = [create_atom("C", [0, 0, 0])]
        ligand = [create_atom("O", [4, 0, 0])]
        
        # Water 1: Bridge (2, 1, 0)
        # Water 2: Too far (10, 10, 10)
        # Water 3: Bridge (2, -1, 0)
        water = [
            create_atom("O", [2, 1, 0]),
            create_atom("O", [10, 10, 10]),
            create_atom("O", [2, -1, 0])
        ]
        
        has_bridge, bridges = detect_water_mediated_interactions(protein, ligand, water)
        assert has_bridge is True
        assert len(bridges) == 2
        # Expected bridges: (0, 0, 0) and (0, 2, 0)
        # Order might depend on iteration, so check content
        indices = set(bridges)
        assert (0, 0, 0) in indices
        assert (0, 2, 0) in indices

    def test_custom_threshold(self):
        """Test with a custom threshold."""
        protein = [create_atom("C", [0, 0, 0])]
        ligand = [create_atom("O", [4, 0, 0])]
        # Water at distance 3.0 from both (sqrt(9+1) = 3.16 > 3.0)
        # But if threshold is 3.5, it should work.
        water = [create_atom("O", [2, 1, 0])]
        
        # Default threshold 3.5
        has_bridge_35, _ = detect_water_mediated_interactions(protein, ligand, water, threshold=3.5)
        assert has_bridge_35 is True
        
        # Custom threshold 2.0 (should fail)
        has_bridge_20, _ = detect_water_mediated_interactions(protein, ligand, water, threshold=2.0)
        assert has_bridge_20 is False
