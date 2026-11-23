"""
Unit tests for the generate_elemental_properties script.
Verifies that the CSV is created with correct headers and data.
"""
import pytest
import csv
import os
from pathlib import Path
import sys

# Add the scripts directory to the path to allow imports if necessary, 
# though we are mostly testing the file generation side-effect.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.generate_elemental_properties import main

class TestElementalPropertiesGeneration:
    
    def test_file_created(self, tmp_path):
        """Test that the script creates the file at the expected location."""
        # We need to patch the output path or run the script in a temp context.
        # Since the script writes to a fixed relative path, we'll verify the 
        # logic by checking if the file exists after running main() in a controlled env.
        # For this test, we assume the script runs relative to its own location.
        # To test robustly, we verify the content structure if the file is generated.
        
        # Note: Running main() writes to code/../data/raw. 
        # In a CI environment or temp test, we might want to mock the path.
        # However, for this specific task, we verify the content of the generated file.
        
        # Let's run the script and check if the file appears in the expected relative location
        # from the script's perspective.
        script_dir = Path(__file__).parent.parent.parent / "code" / "scripts"
        expected_file = script_dir.parent / "data" / "raw" / "elemental_properties.csv"
        
        # Backup existing file if any
        backup = None
        if expected_file.exists():
            backup = expected_file.read_text()
            expected_file.unlink()
        
        try:
            # Run the script
            # The script uses Path(__file__) so we must ensure we are in the right context
            # or we can just import and call main() if it doesn't rely on __file__ for root.
            # The implementation uses Path(__file__).parent, so it is robust.
            success = main()
            assert success is True
            assert expected_file.exists(), "elemental_properties.csv was not created"
        finally:
            # Restore backup if it existed
            if backup is not None:
                expected_file.write_text(backup)
            elif expected_file.exists():
                expected_file.unlink()

    def test_csv_headers(self, tmp_path):
        """Test that the CSV has the correct headers."""
        # Similar setup to create the file
        script_dir = Path(__file__).parent.parent.parent / "code" / "scripts"
        expected_file = script_dir.parent / "data" / "raw" / "elemental_properties.csv"
        
        backup = None
        if expected_file.exists():
            backup = expected_file.read_text()
            expected_file.unlink()
        
        try:
            main()
            with open(expected_file, "r") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                assert "element" in headers
                assert "electronegativity" in headers
                assert "atomic_radii" in headers
                assert "valence_electrons" in headers
        finally:
            if backup is not None:
                expected_file.write_text(backup)
            elif expected_file.exists():
                expected_file.unlink()

    def test_required_elements_present(self):
        """Test that all required elements are present in the generated file."""
        required_elements = {"Mn", "Co", "Fe", "Ga", "Al", "Ni", "Cu", "Sn", "In", "Ti", "V"}
        
        script_dir = Path(__file__).parent.parent.parent / "code" / "scripts"
        expected_file = script_dir.parent / "data" / "raw" / "elemental_properties.csv"
        
        backup = None
        if expected_file.exists():
            backup = expected_file.read_text()
            expected_file.unlink()
        
        try:
            main()
            with open(expected_file, "r") as f:
                reader = csv.DictReader(f)
                found_elements = {row["element"] for row in reader}
            
            assert found_elements == required_elements, f"Missing elements: {required_elements - found_elements}"
        finally:
            if backup is not None:
                expected_file.write_text(backup)
            elif expected_file.exists():
                expected_file.unlink()

    def test_data_types_and_values(self):
        """Test that values are numeric and within reasonable ranges."""
        script_dir = Path(__file__).parent.parent.parent / "code" / "scripts"
        expected_file = script_dir.parent / "data" / "raw" / "elemental_properties.csv"
        
        backup = None
        if expected_file.exists():
            backup = expected_file.read_text()
            expected_file.unlink()
        
        try:
            main()
            with open(expected_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check numeric conversion
                    en = float(row["electronegativity"])
                    ar = float(row["atomic_radii"])
                    ve = int(row["valence_electrons"])
                    
                    # Reasonable range checks
                    assert 1.0 <= en <= 2.5, f"Electronegativity {en} out of expected range for {row['element']}"
                    assert 1.0 <= ar <= 2.0, f"Atomic radii {ar} out of expected range for {row['element']}"
                    assert 3 <= ve <= 11, f"Valence electrons {ve} out of expected range for {row['element']}"
        finally:
            if backup is not None:
                expected_file.write_text(backup)
            elif expected_file.exists():
                expected_file.unlink()