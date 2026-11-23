import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.descriptor_filter import run_vif_analysis, load_descriptors
from config import get_project_root

class TestDescriptorFilterIntegration:
    
    @pytest.fixture
    def mock_descriptors_csv(self, tmp_path):
        """Create a mock descriptors.csv file for testing."""
        # Create a temporary directory structure
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create mock descriptors data
        data = {
            'bulk_config_id': [f'config_{i}' for i in range(50)],
            'impurity_species': ['Cr'] * 50,
            'segregation_energy': np.random.randn(50),
            'rdf_peak': np.random.randn(50) * 2 + 5,
            'pair_corr': np.random.randn(50) * 0.5 + 0.5,
            'voronoi_count': np.random.randint(4, 12, 50)
        }
        df = pd.DataFrame(data)
        
        csv_path = processed_dir / "descriptors.csv"
        df.to_csv(csv_path, index=False)
        
        return csv_path
    
    def test_run_vif_analysis_with_mock_data(self, mock_descriptors_csv):
        """Test the full VIF analysis pipeline with mock data."""
        # We need to temporarily override the project root
        original_root = os.environ.get('PROJECT_ROOT')
        
        try:
            # Set up a temporary project root
            temp_root = mock_descriptors_csv.parent.parent.parent
            os.environ['PROJECT_ROOT'] = str(temp_root)
            
            # Run the analysis
            run_vif_analysis()
            
            # Check that the report was created
            report_path = temp_root / "data" / "processed" / "collinearity_report.md"
            assert report_path.exists(), "Collinearity report was not created"
            
            # Verify report content
            content = report_path.read_text()
            assert "Collinearity Analysis Report" in content
            assert "VIF Scores" in content
            assert "rdf_peak" in content
            assert "pair_corr" in content
            assert "voronoi_count" in content
            
        finally:
            # Restore original environment
            if original_root:
                os.environ['PROJECT_ROOT'] = original_root
            elif 'PROJECT_ROOT' in os.environ:
                del os.environ['PROJECT_ROOT']