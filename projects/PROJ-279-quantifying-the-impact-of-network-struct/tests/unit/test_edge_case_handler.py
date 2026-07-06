"""
Unit tests for edge case handling in graph construction.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
from ase import Atoms
import ase.io

from edge_case_handler import (
    check_file_corruption,
    analyze_coordination_numbers,
    validate_coordination_numbers,
    handle_edge_cases,
    generate_edge_case_report,
    run_edge_case_checks,
    CorruptedFileError,
    UnexpectedCoordinationError
)

class TestCheckFileCorruption:
    def test_file_not_found(self):
        with pytest.raises(CorruptedFileError, match="File not found"):
            check_file_corruption(Path("/nonexistent/file.xyz"))
            
    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with pytest.raises(CorruptedFileError, match="File is empty"):
                check_file_corruption(temp_path)
        finally:
            temp_path.unlink()
            
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode='w') as f:
            f.write("1\n\nC\n")
            temp_path = Path(f.name)
        try:
            is_valid, msg = check_file_corruption(temp_path)
            assert is_valid
            assert "verified" in msg
        finally:
            temp_path.unlink()

class TestAnalyzeCoordinationNumbers:
    def test_simple_lattice(self):
        # Create a simple cubic lattice (coordination = 6 for bulk, but with cutoff)
        atoms = Atoms('C4', 
                     positions=[[0,0,0], [1.5,0,0], [0,1.5,0], [0,0,1.5]],
                     cell=[3,3,3], pbc=True)
        
        # With a large cutoff, all should be neighbors
        coords = analyze_coordination_numbers(atoms, cutoff=2.0)
        
        # Each atom should have 3 neighbors in this tiny cluster
        assert 3 in coords
        assert len(coords[3]) == 4

class TestValidateCoordinationNumbers:
    def test_valid_coordination(self):
        # Create a configuration with expected coordination
        atoms = Atoms('C2', 
                     positions=[[0,0,0], [1.5,1.5,1.5]],
                     cell=[3,3,3], pbc=True)
        
        is_valid, warnings, invalid = validate_coordination_numbers(atoms, "test", cutoff=2.0)
        assert is_valid
        assert len(warnings) == 0
        assert len(invalid) == 0
        
    def test_invalid_coordination(self):
        # Create a configuration with very low coordination (isolated atom)
        atoms = Atoms('C1', positions=[[0,0,0]], cell=[3,3,3], pbc=True)
        
        is_valid, warnings, invalid = validate_coordination_numbers(atoms, "test", cutoff=1.0)
        assert not is_valid
        assert len(warnings) > 0
        assert len(invalid) == 1

class TestHandleEdgeCases:
    def test_corrupted_file_abort(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)
        try:
            # Write garbage
            with open(temp_path, 'wb') as f:
                f.write(b'\x00\x01\x02\x03')
                
            with pytest.raises(CorruptedFileError):
                handle_edge_cases(temp_path, "test", mode="abort")
        finally:
            temp_path.unlink()
            
    def test_corrupted_file_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with open(temp_path, 'wb') as f:
                f.write(b'\x00\x01\x02\x03')
                
            atoms, warnings = handle_edge_cases(temp_path, "test", mode="flag")
            assert atoms is None
            assert len(warnings) > 0
            assert "Corruption" in str(warnings[0])
        finally:
            temp_path.unlink()
            
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode='w') as f:
            f.write("2\n\nC 0 0 0\nC 1.5 1.5 1.5\n")
            temp_path = Path(f.name)
        try:
            atoms, warnings = handle_edge_cases(temp_path, "test", mode="abort")
            assert atoms is not None
            assert len(atoms) == 2
            assert len(warnings) == 0
        finally:
            temp_path.unlink()

class TestGenerateEdgeCaseReport:
    def test_report_generation(self):
        results = [
            {"config_id": "test1", "status": "valid", "reason": "", "warnings": []},
            {"config_id": "test2", "status": "corrupted", "reason": "Bad file", "warnings": []}
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
            
        try:
            generate_edge_case_report(results, temp_path)
            
            with open(temp_path) as f:
                report = json.load(f)
                
            assert report["summary"]["total_processed"] == 2
            assert report["summary"]["corrupted"] == 1
            assert report["summary"]["valid"] == 1
        finally:
            temp_path.unlink()

class TestRunEdgeCaseChecks:
    def test_run_checks(self):
        # Create temporary valid and invalid files
        valid_file = tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode='w')
        valid_file.write("2\n\nC 0 0 0\nC 1.5 1.5 1.5\n")
        valid_file.close()
        
        invalid_file = tempfile.NamedTemporaryFile(suffix=".xyz", delete=False)
        invalid_file.write(b'\x00\x01\x02')
        invalid_file.close()
        
        try:
            results = run_edge_case_checks(
                [Path(valid_file.name), Path(invalid_file.name)],
                mode="flag"
            )
            
            assert len(results) == 2
            
            # Check valid file result
            valid_result = next(r for r in results if "valid" in r["file_path"])
            assert valid_result["status"] == "valid"
            
            # Check invalid file result
            invalid_result = next(r for r in results if "invalid" in r["file_path"] or "tmp" in r["file_path"] and r["file_path"] != valid_file.name)
            assert invalid_result["status"] in ["corrupted", "error"]
            
        finally:
            Path(valid_file.name).unlink()
            Path(invalid_file.name).unlink()