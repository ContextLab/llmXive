"""
Unit tests for metrics_calc.py
Specifically tests for Gini coefficient calculation (T019).
"""
import pytest
import math
import csv
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics_calc import calculate_gini, calculate_module_gini_metrics, load_ownership_csv

class TestGiniCoefficient:
    """Tests for the Gini coefficient calculation."""
    
    def test_gini_perfect_equality(self):
        """When all values are equal, Gini should be 0."""
        values = [10, 10, 10, 10, 10]
        gini = calculate_gini(values)
        assert abs(gini - 0.0) < 0.001
        
    def test_gini_perfect_inequality(self):
        """When one person has everything, Gini should be 1."""
        values = [0, 0, 0, 0, 100]
        gini = calculate_gini(values)
        assert abs(gini - 1.0) < 0.001
        
    def test_gini_empty_list(self):
        """Empty list should return 0."""
        gini = calculate_gini([])
        assert gini == 0.0
        
    def test_gini_single_value(self):
        """Single value should return 0."""
        gini = calculate_gini([100])
        assert gini == 0.0
        
    def test_gini_all_zeros(self):
        """All zeros should return 0."""
        gini = calculate_gini([0, 0, 0, 0])
        assert gini == 0.0
        
    def test_gini_known_value(self):
        """Test against a known Gini value."""
        # Example: [1, 2, 3, 4, 5]
        # Sorted: [1, 2, 3, 4, 5]
        # n=5, sum=15
        # numerator = 2*(1*1 + 2*2 + 3*3 + 4*4 + 5*5) - 6*15
        #           = 2*(1+4+9+16+25) - 90
        #           = 2*55 - 90 = 110 - 90 = 20
        # gini = 20 / (5 * 15) = 20/75 = 0.2666...
        values = [1, 2, 3, 4, 5]
        gini = calculate_gini(values)
        expected = 20 / 75
        assert abs(gini - expected) < 0.001
        
    def test_gini_precision(self):
        """Test that Gini is calculated with sufficient precision."""
        values = [1, 1, 1, 1, 100]
        gini = calculate_gini(values)
        # Should be high but not exactly 1
        assert gini > 0.5
        assert gini < 1.0
        
    def test_gini_negative_values_handling(self):
        """Gini should handle negative values gracefully (though not expected in ownership)."""
        # With negative values, the formula might not make sense, but it shouldn't crash
        values = [-5, -5, -5]
        # This might produce unexpected results but shouldn't crash
        gini = calculate_gini(values)
        # The function should return a valid float
        assert isinstance(gini, float)

class TestModuleGiniCalculation:
    """Tests for the full module Gini calculation pipeline."""
    
    def test_load_ownership_csv_pre_aggregated(self):
        """Test loading a pre-aggregated ownership CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['module_path', 'author', 'count'])
            writer.writerow(['module1.py', 'alice', '10'])
            writer.writerow(['module1.py', 'bob', '5'])
            writer.writerow(['module2.py', 'charlie', '20'])
            temp_path = Path(f.name)
        
        try:
            result = load_ownership_csv(temp_path)
            
            assert 'module1.py' in result
            assert 'module2.py' in result
            
            # Check module1
            module1_authors = dict(result['module1.py'])
            assert module1_authors['alice'] == 10
            assert module1_authors['bob'] == 5
            
            # Check module2
            module2_authors = dict(result['module2.py'])
            assert module2_authors['charlie'] == 20
        finally:
            temp_path.unlink()
            
    def test_load_ownership_csv_raw(self):
        """Test loading a raw ownership CSV (one row per commit)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['module_path', 'author'])
            writer.writerow(['module1.py', 'alice'])
            writer.writerow(['module1.py', 'alice'])
            writer.writerow(['module1.py', 'bob'])
            writer.writerow(['module2.py', 'charlie'])
            writer.writerow(['module2.py', 'charlie'])
            writer.writerow(['module2.py', 'charlie'])
            temp_path = Path(f.name)
        
        try:
            result = load_ownership_csv(temp_path)
            
            assert 'module1.py' in result
            assert 'module2.py' in result
            
            # Check module1: alice=2, bob=1
            module1_authors = dict(result['module1.py'])
            assert module1_authors['alice'] == 2
            assert module1_authors['bob'] == 1
            
            # Check module2: charlie=3
            module2_authors = dict(result['module2.py'])
            assert module2_authors['charlie'] == 3
        finally:
            temp_path.unlink()
            
    def test_calculate_module_gini_metrics(self):
        """Test the full Gini calculation for modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            # Create test ownership CSV
            input_csv = input_dir / "test_ownership.csv"
            with open(input_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['module_path', 'author', 'count'])
                # Module with perfect equality (Gini = 0)
                writer.writerow(['equal_module.py', 'alice', '10'])
                writer.writerow(['equal_module.py', 'bob', '10'])
                # Module with high inequality (Gini > 0.5)
                writer.writerow(['inequal_module.py', 'alice', '10'])
                writer.writerow(['inequal_module.py', 'bob', '1'])
                
            output_csv = output_dir / "test_gini.csv"
            
            calculate_module_gini_metrics(input_csv, output_csv)
            
            # Verify output file exists
            assert output_csv.exists()
            
            # Read and verify results
            with open(output_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            
            # Find rows by module name
            equal_row = next(r for r in rows if r['module_path'] == 'equal_module.py')
            inequal_row = next(r for r in rows if r['module_path'] == 'inequal_module.py')
            
            # Check equality module
            assert float(equal_row['gini_coefficient']) < 0.01
            assert int(equal_row['num_authors']) == 2
            assert int(equal_row['total_commits']) == 20
            
            # Check inequality module
            gini_val = float(inequal_row['gini_coefficient'])
            assert gini_val > 0.5
            assert gini_val < 1.0
            assert int(inequal_row['num_authors']) == 2
            assert int(inequal_row['total_commits']) == 11

if __name__ == "__main__":
    pytest.main([__file__, "-v"])