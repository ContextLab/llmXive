import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Import the functions to test from the actual module
from src.meta_analysis import (
    load_gene_panel,
    calculate_meta_analysis_bonferroni,
    write_bonferroni_correction,
    main
)
from src.config import get_project_root

class TestCalculateMetaAnalysisBonferroni:
    """Unit tests for the m_meta calculation logic in T024d."""

    def test_calculate_m_meta_valid_panel(self, tmp_path):
        """Test calculation with a valid panel containing selected genes."""
        panel_data = {
            "selected": [
                {"gene_symbol": "GENE1", "meta_p_value": 0.001},
                {"gene_symbol": "GENE2", "meta_p_value": 0.002},
                {"gene_symbol": "GENE3", "meta_p_value": 0.003}
            ],
            "fallback_reason": "intersection_empty"
        }
        
        m_meta = calculate_meta_analysis_bonferroni(panel_data)
        
        assert m_meta == 3
        assert isinstance(m_meta, int)

    def test_calculate_m_meta_empty_panel_raises(self, tmp_path):
        """Test that an empty selected list raises ValueError."""
        panel_data = {
            "selected": [],
            "fallback_reason": "intersection_empty"
        }
        
        with pytest.raises(ValueError, match="selected.*list is empty"):
            calculate_meta_analysis_bonferroni(panel_data)

    def test_calculate_m_meta_missing_key_raises(self, tmp_path):
        """Test that missing 'selected' key raises ValueError."""
        panel_data = {
            "fallback_reason": "intersection_empty"
        }
        
        with pytest.raises(ValueError, match="missing.*selected"):
            calculate_meta_analysis_bonferroni(panel_data)

    def test_calculate_m_meta_wrong_type_raises(self, tmp_path):
        """Test that non-list 'selected' raises ValueError."""
        panel_data = {
            "selected": "GENE1,GENE2",
            "fallback_reason": "intersection_empty"
        }
        
        with pytest.raises(ValueError, match="must be a list"):
            calculate_meta_analysis_bonferroni(panel_data)

class TestWriteBonferroniCorrection:
    """Unit tests for writing the Bonferroni correction file."""

    def test_write_bonferroni_creates_file(self, tmp_path):
        """Test that the output file is created with correct content."""
        m_meta = 5
        output_path = tmp_path / "bonferroni_correction.json"
        
        write_bonferroni_correction(m_meta, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["m_meta"] == 5
        assert "description" in data
        assert "alpha_threshold" in data
        assert data["alpha_threshold"] == pytest.approx(0.01 / 5)

    def test_write_bonferroni_creates_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        m_meta = 10
        output_path = tmp_path / "subdir" / "deep" / "bonferroni_correction.json"
        
        write_bonferroni_correction(m_meta, output_path)
        
        assert output_path.exists()
        assert output_path.parent.exists()

class TestMainFunction:
    """Integration-style tests for the main() entry point."""

    def test_main_success(self, tmp_path):
        """Test successful execution of main() with valid inputs."""
        # Create mock project structure
        results_dir = tmp_path / "results" / "meta_analysis"
        results_dir.mkdir(parents=True)
        
        # Create a valid gene panel
        panel_data = {
            "selected": [
                {"gene_symbol": "GENE1", "meta_p_value": 0.001},
                {"gene_symbol": "GENE2", "meta_p_value": 0.002}
            ]
        }
        panel_path = results_dir / "gene_panel.json"
        with open(panel_path, 'w') as f:
            json.dump(panel_data, f)
        
        # Mock get_project_root to use tmp_path
        original_get_project_root = get_project_root
        import src.meta_analysis as ma_module
        ma_module.get_project_root = lambda: tmp_path
        
        try:
            result = main()
            assert result == 0
            
            # Verify output file was created
            output_path = tmp_path / "results" / "meta_analysis" / "bonferroni_correction.json"
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["m_meta"] == 2
        finally:
            ma_module.get_project_root = original_get_project_root

    def test_main_missing_panel_file(self, tmp_path):
        """Test that main() returns 1 when gene panel is missing."""
        # Create empty results directory without gene_panel.json
        results_dir = tmp_path / "results" / "meta_analysis"
        results_dir.mkdir(parents=True)
        
        # Mock get_project_root
        original_get_project_root = get_project_root
        import src.meta_analysis as ma_module
        ma_module.get_project_root = lambda: tmp_path
        
        try:
            result = main()
            assert result == 1
        finally:
            ma_module.get_project_root = original_get_project_root

    def test_main_empty_selected_list(self, tmp_path):
        """Test that main() returns 1 when selected list is empty."""
        # Create mock project structure
        results_dir = tmp_path / "results" / "meta_analysis"
        results_dir.mkdir(parents=True)
        
        # Create gene panel with empty selected list
        panel_data = {"selected": []}
        panel_path = results_dir / "gene_panel.json"
        with open(panel_path, 'w') as f:
            json.dump(panel_data, f)
        
        # Mock get_project_root
        original_get_project_root = get_project_root
        import src.meta_analysis as ma_module
        ma_module.get_project_root = lambda: tmp_path
        
        try:
            result = main()
            assert result == 1
        finally:
            ma_module.get_project_root = original_get_project_root