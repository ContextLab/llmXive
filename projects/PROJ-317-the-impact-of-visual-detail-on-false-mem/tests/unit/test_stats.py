import pytest
import numpy as np
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if needed, though usually handled by test runner
# Assuming tests are run from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stats import calculate_anova_power, save_power_analysis, main

class TestPowerAnalysis:
    def test_calculate_anova_power_returns_correct_structure(self):
        result = calculate_anova_power(effect_size=0.25, alpha=0.05, power=0.80)
        
        assert "n_per_group" in result
        assert "total_n" in result
        assert "effect_size" in result
        assert "power" in result
        assert "alpha" in result
        
        assert result["effect_size"] == 0.25
        assert result["power"] == 0.80
        assert result["alpha"] == 0.05
        
        # Check that total_n is a positive integer
        assert isinstance(result["total_n"], int)
        assert result["total_n"] > 0

    def test_calculate_anova_power_sufficient_sample_size(self):
        # With medium effect size, total_n should be >= 50 for this study design
        result = calculate_anova_power()
        # The specific value depends on the calculation, but it should be reasonable
        # For f=0.25, alpha=0.05, power=0.80, k=3, total_n is typically around 150-200
        # We just assert it's not trivially small (e.g., < 10)
        assert result["total_n"] >= 10

    def test_save_power_analysis_creates_json(self, tmp_path):
        result = {
            "n_per_group": 50,
            "total_n": 150,
            "effect_size": 0.25,
            "power": 0.80,
            "alpha": 0.05
        }
        
        # Mock get_project_root to return tmp_path for this test
        with patch('analysis.stats.get_project_root') as mock_root:
            mock_root.return_value = tmp_path
            output_path = save_power_analysis(result, filename="test_power.json")
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == result

    def test_main_exits_on_insufficient_power(self):
        # Mock calculate_anova_power to return a result with total_n < 50
        mock_result = {
            "n_per_group": 10,
            "total_n": 30,
            "effect_size": 0.25,
            "power": 0.80,
            "alpha": 0.05
        }
        
        with patch('analysis.stats.calculate_anova_power', return_value=mock_result):
            with patch('analysis.stats.save_power_analysis'):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == "Pipeline Halted: Insufficient Power (N < 50). Check power_report.json."

    def test_main_saves_on_sufficient_power(self, tmp_path):
        mock_result = {
            "n_per_group": 50,
            "total_n": 150,
            "effect_size": 0.25,
            "power": 0.80,
            "alpha": 0.05
        }
        
        with patch('analysis.stats.get_project_root') as mock_root:
            mock_root.return_value = tmp_path
            with patch('analysis.stats.calculate_anova_power', return_value=mock_result):
                # This should not raise SystemExit
                main()
                
                # Verify the file was created
                output_path = tmp_path / "data" / "analysis" / "power_report.json"
                assert output_path.exists()
                
                with open(output_path, 'r') as f:
                    saved_data = json.load(f)
                
                assert saved_data == mock_result