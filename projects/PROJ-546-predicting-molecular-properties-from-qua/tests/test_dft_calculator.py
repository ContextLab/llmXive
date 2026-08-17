import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from dft_calculator import (
    load_subset_indices,
    get_geometry_path,
    parse_xyz_to_psi4_input,
    generate_locked_splits,
    write_locked_splits
)

class TestDFTCalculator:

    def test_load_subset_indices_valid(self, tmp_path):
        subset_file = tmp_path / "subset.json"
        data = [1, 2, 3]
        with open(subset_file, 'w') as f:
            json.dump(data, f)
        
        result = load_subset_indices(str(subset_file))
        assert result == [1, 2, 3]

    def test_load_subset_indices_invalid_format(self, tmp_path):
        subset_file = tmp_path / "subset.json"
        with open(subset_file, 'w') as f:
            json.dump({"not": "list"}, f)
        
        with pytest.raises(ValueError):
            load_subset_indices(str(subset_file))

    def test_load_subset_indices_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_subset_indices("nonexistent.json")

    def test_get_geometry_path_valid(self, tmp_path):
        geom_dir = tmp_path / "optimized_geometries"
        geom_dir.mkdir()
        (geom_dir / "molecule_123.xyz").touch()
        
        path = get_geometry_path(123, base_dir=str(geom_dir))
        assert path.exists()
        assert path.name == "molecule_123.xyz"

    def test_get_geometry_path_not_found(self, tmp_path):
        geom_dir = tmp_path / "optimized_geometries"
        geom_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            get_geometry_path(999, base_dir=str(geom_dir))

    def test_parse_xyz_to_psi4_input(self, tmp_path):
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """2
        Test molecule
        C 0.0 0.0 0.0
        H 0.0 0.0 1.0
        """
        with open(xyz_file, 'w') as f:
            f.write(xyz_content)
        
        psi4_input = parse_xyz_to_psi4_input(xyz_file)
        assert "C 0.0 0.0 0.0" in psi4_input
        assert "H 0.0 0.0 1.0" in psi4_input
        assert "B3LYP" in psi4_input
        assert "def2-SVP" in psi4_input

    def test_generate_locked_splits(self):
        splits = generate_locked_splits(10, n_folds=2, random_state=42)
        assert len(splits) == 2
        for train, test in splits:
            assert len(train) + len(test) == 10
            assert set(train) & set(test) == set()

    def test_write_locked_splits(self, tmp_path):
        splits = [([0, 1], [2, 3]), ([2, 3], [0, 1])]
        output_file = tmp_path / "splits.json"
        write_locked_splits(splits, str(output_file))
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == splits