import pytest
import pandas as pd
import os
import json
import tempfile
from pathlib import Path

# Import the function to test
from preprocessing import classify_alloy_family, generate_alloy_class_map

class TestAlloyClassification:
    
    def test_high_entropy_alloy_logic(self):
        """Test that 5+ elements > 5% correctly identifies High-Entropy Alloy."""
        # Create a mock row with 5 elements > 5%
        row_data = {
            'record_id': 'test_he_01',
            'fe': 15.0, 'cr': 15.0, 'ni': 15.0, 'mn': 15.0, 'co': 15.0, # 5 elements > 5%
            'c': 0.1, 'si': 0.1
        }
        row = pd.Series(row_data)
        result = classify_alloy_family(row)
        assert result == "High-Entropy Alloy", f"Expected High-Entropy Alloy, got {result}"

    def test_stainless_steel_logic(self):
        """Test that Fe > 10% AND Cr > 10% correctly identifies Stainless Steel."""
        row_data = {
            'record_id': 'test_ss_01',
            'fe': 70.0, 'cr': 18.0, 'ni': 8.0,
            'c': 0.1, 'mn': 1.0
        }
        row = pd.Series(row_data)
        result = classify_alloy_family(row)
        assert result == "Stainless Steel", f"Expected Stainless Steel, got {result}"

    def test_carbon_steel_logic(self):
        """Test that Fe > 80% AND C < 2% correctly identifies Carbon Steel."""
        row_data = {
            'record_id': 'test_cs_01',
            'fe': 98.0, 'c': 0.5, 'mn': 1.0,
            'si': 0.2
        }
        row = pd.Series(row_data)
        result = classify_alloy_family(row)
        assert result == "Carbon Steel", f"Expected Carbon Steel, got {result}"

    def test_other_logic(self):
        """Test that records not matching specific rules are classified as Other."""
        row_data = {
            'record_id': 'test_other_01',
            'fe': 5.0, 'c': 0.1, 'cu': 90.0, # Copper based, not steel
            'zn': 5.0
        }
        row = pd.Series(row_data)
        result = classify_alloy_family(row)
        assert result == "Other", f"Expected Other, got {result}"

    def test_priority_rules(self):
        """Test that High-Entropy rule takes priority over Stainless Steel."""
        # Fe=15, Cr=15 (Stainless condition), but also Ni=15, Mn=15, Co=15 (HE condition)
        row_data = {
            'record_id': 'test_priority_01',
            'fe': 15.0, 'cr': 15.0, 'ni': 15.0, 'mn': 15.0, 'co': 15.0,
            'c': 0.1
        }
        row = pd.Series(row_data)
        result = classify_alloy_family(row)
        # Should be HE because 5 elements > 5%
        assert result == "High-Entropy Alloy", f"Expected High-Entropy Alloy (priority), got {result}"

class TestGenerateAlloyClassMap:
    
    def test_generate_map_from_csv(self):
        """Test generating the alloy class map from a temporary CSV file."""
        # Create temporary directory and files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "cleaned_alloys.csv")
            output_path = os.path.join(tmpdir, "alloy_class_map.json")
            
            # Create mock CSV data
            data = {
                'record_id': ['rec_001', 'rec_002', 'rec_003', 'rec_004'],
                'fe': [70.0, 98.0, 15.0, 5.0],
                'cr': [18.0, 1.0, 15.0, 0.0],
                'ni': [8.0, 1.0, 15.0, 0.0],
                'mn': [1.0, 1.0, 15.0, 0.0],
                'co': [0.0, 0.0, 15.0, 0.0],
                'c': [0.1, 0.5, 0.1, 0.1]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            # Run the function
            result_map = generate_alloy_class_map(input_path, output_path)
            
            # Verify output file exists
            assert os.path.exists(output_path), "Output JSON file was not created"
            
            # Verify content
            with open(output_path, 'r') as f:
                loaded_map = json.load(f)
            
            assert loaded_map['rec_001'] == "Stainless Steel"
            assert loaded_map['rec_002'] == "Carbon Steel"
            assert loaded_map['rec_003'] == "High-Entropy Alloy"
            assert loaded_map['rec_004'] == "Other"
            
            assert len(result_map) == 4