"""
Unit tests for the fitting engine (T023).
"""

import numpy as np
import pytest
from pathlib import Path

from fit import fit_mond_galaxy, fit_nfw_galaxy, fit_galaxy


class TestFittingEngine:
    """Tests for the fitting engine functionality."""

    @pytest.fixture
    def sample_rotation_curve(self):
        """Create a sample rotation curve for testing."""
        r = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        v = np.array([100.0, 150.0, 180.0, 200.0, 210.0, 215.0, 218.0, 220.0, 221.0, 222.0])
        v_err = np.array([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        return r, v, v_err

    def test_mond_fit_convergence(self, sample_rotation_curve):
        """Test that MOND fit converges on reasonable data."""
        r, v, v_err = sample_rotation_curve
        params, cov, success = fit_mond_galaxy(r, v, v_err)
        
        assert success is True, "MOND fit should converge on sample data"
        assert params is not None
        assert 'm_l' in params
        assert params['m_l'] > 0.1
        assert params['m_l'] < 2.0
        assert 'a0' in params
        assert params['n_dof'] == len(r) - 1

    def test_mond_fit_bounds(self, sample_rotation_curve):
        """Test that MOND fit respects parameter bounds."""
        r, v, v_err = sample_rotation_curve
        m_l_bounds = (0.2, 1.5)
        params, cov, success = fit_mond_galaxy(
            r, v, v_err, 
            m_l_bounds=m_l_bounds
        )
        
        assert success is True
        assert m_l_bounds[0] <= params['m_l'] <= m_l_bounds[1]

    def test_nfw_fit_convergence(self, sample_rotation_curve):
        """Test that NFW fit converges on reasonable data."""
        r, v, v_err = sample_rotation_curve
        m_baryon = 1e10  # 10^10 Msun
        params, cov, success = fit_nfw_galaxy(r, v, v_err, m_baryon)
        
        assert success is True, "NFW fit should converge on sample data"
        assert params is not None
        assert 'm_l' in params
        assert 'c' in params
        assert params['m_l'] > 0.1
        assert params['m_l'] < 2.0
        assert params['c'] > 1.0
        assert params['c'] < 50.0
        assert params['n_dof'] == len(r) - 2

    def test_nfw_fit_with_prior(self, sample_rotation_curve):
        """Test NFW fit with concentration prior."""
        r, v, v_err = sample_rotation_curve
        m_baryon = 5e10  # 5 * 10^10 Msun
        params, cov, success = fit_nfw_galaxy(r, v, v_err, m_baryon)
        
        assert success is True
        # Higher mass should generally lead to different concentration
        assert 'c' in params

    def test_fit_galaxy_mond(self, sample_rotation_curve):
        """Test the high-level fit_galaxy function for MOND."""
        r, v, v_err = sample_rotation_curve
        galaxy_data = {
            'id': 'test_galaxy_1',
            'name': 'Test Galaxy',
            'r': r,
            'v': v,
            'v_err': v_err,
            'm_baryon': 1e10
        }
        
        result = fit_galaxy(galaxy_data, model_type='mond')
        
        assert result['success'] is True
        assert result['model'] == 'mond'
        assert result['galaxy_name'] == 'Test Galaxy'
        assert 'm_l' in result
        assert result['n_points'] == len(r)

    def test_fit_galaxy_nfw(self, sample_rotation_curve):
        """Test the high-level fit_galaxy function for NFW."""
        r, v, v_err = sample_rotation_curve
        galaxy_data = {
            'id': 'test_galaxy_2',
            'name': 'Test Galaxy NFW',
            'r': r,
            'v': v,
            'v_err': v_err,
            'm_baryon': 1e10
        }
        
        result = fit_galaxy(galaxy_data, model_type='nfw')
        
        assert result['success'] is True
        assert result['model'] == 'nfw'
        assert 'm_l' in result
        assert 'c' in result

    def test_fit_galaxy_insufficient_data(self):
        """Test fitting with insufficient data points."""
        r = np.array([1.0, 2.0])  # Only 2 points
        v = np.array([100.0, 150.0])
        v_err = np.array([5.0, 5.0])
        
        galaxy_data = {
            'id': 'test_galaxy_3',
            'name': 'Too Few Points',
            'r': r,
            'v': v,
            'v_err': v_err
        }
        
        result = fit_galaxy(galaxy_data, model_type='mond')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Insufficient data points' in result['error']

    def test_fit_galaxy_nfw_missing_m_baryon(self, sample_rotation_curve):
        """Test NFW fit without baryonic mass."""
        r, v, v_err = sample_rotation_curve
        galaxy_data = {
            'id': 'test_galaxy_4',
            'name': 'Missing Mass',
            'r': r,
            'v': v,
            'v_err': v_err
            # Missing 'm_baryon'
        }
        
        result = fit_galaxy(galaxy_data, model_type='nfw')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Missing m_baryon' in result['error']

    def test_fit_galaxy_unknown_model(self, sample_rotation_curve):
        """Test fitting with unknown model type."""
        r, v, v_err = sample_rotation_curve
        galaxy_data = {
            'id': 'test_galaxy_5',
            'name': 'Unknown Model',
            'r': r,
            'v': v,
            'v_err': v_err
        }
        
        result = fit_galaxy(galaxy_data, model_type='unknown')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Unknown model type' in result['error']

    def test_fit_with_zero_uncertainties(self, sample_rotation_curve):
        """Test fitting when some uncertainties are zero."""
        r, v, v_err = sample_rotation_curve
        # Set some uncertainties to zero
        v_err[0] = 0.0
        v_err[2] = 0.0
        
        galaxy_data = {
            'id': 'test_galaxy_6',
            'name': 'Zero Uncertainties',
            'r': r,
            'v': v,
            'v_err': v_err
        }
        
        # Should filter out zero uncertainties and still work
        result = fit_galaxy(galaxy_data, model_type='mond')
        
        # Should succeed with remaining points
        assert result['success'] is True
        assert result['n_points'] < len(r)  # Some points filtered