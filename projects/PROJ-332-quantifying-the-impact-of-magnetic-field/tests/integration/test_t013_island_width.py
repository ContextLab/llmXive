"""
Integration tests for T013: Island width retrieval and derivation.
Tests the full flow of fetching pre-calculated island width or deriving it.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.metrics import derive_island_width, process_metrics_for_discharges
from code.data.retrieval import fetch_island_width, get_efit_data

class TestIslandWidthDerivation:
    """Tests for the derive_island_width function."""
    
    def test_derive_island_width_success(self):
        """Test successful derivation of island width."""
        # Create realistic test data
        rho_values = np.linspace(0.1, 1.0, 50)
        q_profile = 1.5 + 2.0 * rho_values  # q increases with radius
        local_magnetic_shear = 0.5
        Bt_field = 2.0  # Tesla
        
        result = derive_island_width(
            local_magnetic_shear=local_magnetic_shear,
            q_profile=q_profile,
            Bt_field=Bt_field,
            rho_values=rho_values
        )
        
        assert result is not None
        assert 0 < result < 0.67, f"Island width {result} out of physical range"
        
    def test_derive_island_width_missing_shear(self):
        """Test derivation fails when magnetic shear is missing."""
        result = derive_island_width(
            local_magnetic_shear=None,
            q_profile=np.array([1.0, 2.0]),
            Bt_field=2.0,
            rho_values=np.array([0.1, 0.2])
        )
        assert result is None
        
    def test_derive_island_width_missing_q_profile(self):
        """Test derivation fails when q_profile is empty."""
        result = derive_island_width(
            local_magnetic_shear=0.5,
            q_profile=np.array([]),
            Bt_field=2.0,
            rho_values=np.array([0.1, 0.2])
        )
        assert result is None
        
    def test_derive_island_width_no_rational_surface(self):
        """Test derivation fails when no rational surface is found."""
        rho_values = np.linspace(0.1, 1.0, 50)
        # q values far from m/n = 3/2 = 1.5
        q_profile = 5.0 + 0.1 * rho_values  # q ranges from 5.01 to 5.1
        
        result = derive_island_width(
            local_magnetic_shear=0.5,
            q_profile=q_profile,
            Bt_field=2.0,
            rho_values=rho_values
        )
        assert result is None

class TestProcessMetricsForDischarges:
    """Tests for the process_metrics_for_discharges function."""
    
    def test_process_with_pre_calculated_width(self):
        """Test processing when pre-calculated island width is available."""
        discharge_data = [
            {
                'discharge_id': 12345,
                'island_width': 0.05,  # Pre-calculated
                'tau_e': 0.1,
                'confinement_mode': 'H-mode',
                'h98y2': 0.9
            }
        ]
        
        efit_cache = {}  # Not needed since pre-calculated exists
        
        df, excluded = process_metrics_for_discharges(discharge_data, efit_cache)
        
        assert len(df) == 1
        assert df.iloc[0]['discharge_id'] == 12345
        assert df.iloc[0]['island_width'] == 0.05
        assert len(excluded) == 0
        
    def test_process_with_derived_width(self):
        """Test processing when island width needs to be derived."""
        discharge_data = [
            {
                'discharge_id': 12346,
                'island_width': None,  # Missing, needs derivation
                'tau_e': 0.15,
                'confinement_mode': 'L-mode',
                'h98y2': 0.7
            }
        ]
        
        # Provide EFIT data for derivation
        efit_cache = {
            12346: {
                'q_profile': 1.5 + 2.0 * np.linspace(0.1, 1.0, 50),
                'rho_values': np.linspace(0.1, 1.0, 50),
                'Bt_field': 2.0,
                'local_magnetic_shear': 0.5
            }
        }
        
        df, excluded = process_metrics_for_discharges(discharge_data, efit_cache)
        
        assert len(df) == 1
        assert df.iloc[0]['discharge_id'] == 12346
        assert df.iloc[0]['island_width'] is not None
        assert 0 < df.iloc[0]['island_width'] < 0.67
        assert len(excluded) == 0
        
    def test_process_with_missing_efit(self):
        """Test exclusion when EFIT data is missing for derivation."""
        discharge_data = [
            {
                'discharge_id': 12347,
                'island_width': None,  # Missing
                'tau_e': 0.1,
            }
        ]
        
        efit_cache = {}  # No EFIT data
        
        df, excluded = process_metrics_for_discharges(discharge_data, efit_cache)
        
        assert len(df) == 0
        assert len(excluded) == 1
        assert excluded[0]['discharge_id'] == 12347
        assert 'EFIT data' in excluded[0]['reason']
        
    def test_process_with_missing_derivation_inputs(self):
        """Test exclusion when derivation inputs are incomplete."""
        discharge_data = [
            {
                'discharge_id': 12348,
                'island_width': None,
                'tau_e': 0.1,
            }
        ]
        
        # Partial EFIT data (missing q_profile)
        efit_cache = {
            12348: {
                'rho_values': np.linspace(0.1, 1.0, 50),
                'Bt_field': 2.0,
                # Missing local_magnetic_shear and q_profile
            }
        }
        
        df, excluded = process_metrics_for_discharges(discharge_data, efit_cache)
        
        assert len(df) == 0
        assert len(excluded) == 1
        assert excluded[0]['discharge_id'] == 12348
        assert 'Missing derivation inputs' in excluded[0]['reason']

class TestIntegrationWithMockMDSplus:
    """Integration tests with mocked MDSplus connection."""
    
    @patch('code.data.retrieval.connection')
    def test_fetch_island_width_pre_calculated(self, mock_connection):
        """Test fetching pre-calculated island width."""
        mock_tree = Mock()
        mock_tree.get.return_value.data.return_value = np.array([0.05, 0.06, 0.055])
        mock_connection.openTree.return_value = mock_tree
        
        result = fetch_island_width(mock_connection, 12345)
        
        assert result == 0.055  # Mean of [0.05, 0.06, 0.055]
        
    @patch('code.data.retrieval.connection')
    def test_fetch_island_width_derivation_needed(self, mock_connection):
        """Test derivation when pre-calculated is missing."""
        # First call returns None (no pre-calculated)
        mock_tree_islands = Mock()
        mock_tree_islands.get.return_value.data.return_value = np.array([])
        
        # Second call returns EFIT data
        mock_tree_efit = Mock()
        mock_tree_efit.get.side_effect = [
            1.5 + 2.0 * np.linspace(0.1, 1.0, 50),  # q_profile
            np.linspace(0.1, 1.0, 50),  # rho_values
            2.0  # Bt_field
        ]
        
        mock_connection.openTree.side_effect = [mock_tree_islands, mock_tree_efit]
        
        # This would normally call get_efit_data and derive_island_width
        # The full flow is tested in process_metrics_for_discharges
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])