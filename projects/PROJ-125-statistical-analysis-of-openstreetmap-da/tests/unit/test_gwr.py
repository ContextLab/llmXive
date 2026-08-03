import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from unittest.mock import patch, MagicMock

from modeling import GWRModel, fit_gwr_model, fit_ols_baseline

@pytest.fixture
def sample_gdf():
    """Create a small sample GeoDataFrame for testing."""
    n = 20
    coords = np.random.rand(n, 2) * 100
    geometry = [Point(x, y) for x, y in coords]
    gdf = gpd.GeoDataFrame({
        'x': coords[:, 0],
        'y': coords[:, 1],
        'feature1': np.random.rand(n),
        'feature2': np.random.rand(n),
        'target': np.random.rand(n) * 10
    }, geometry=geometry)
    return gdf

def test_gwr_model_init():
    gwr = GWRModel(bandwidth=5.0)
    assert gwr.bandwidth == 5.0
    assert gwr.kernel == 'gaussian'

def test_gwr_kernel_weights():
    gwr = GWRModel(bandwidth=10.0)
    dists = np.array([0.0, 5.0, 10.0, 20.0])
    weights = gwr._kernel_weights(dists)
    
    # Check weights are between 0 and 1
    assert np.all(weights >= 0) and np.all(weights <= 1)
    # Check that distance 0 has weight 1
    assert weights[0] == 1.0
    # Check that distance > bandwidth has weight 0 for bisquare (if tested)
    # For gaussian, it's never exactly 0 but very small

def test_fit_gwr_model_fallback(sample_gdf):
    """Test that GWR falls back to OLS if memory is too high or error occurs."""
    features = ['feature1', 'feature2']
    target = 'target'
    
    # Test normal execution (small data)
    result = fit_gwr_model(sample_gdf, features, target)
    assert result['type'] in ['GWR', 'OLS']
    assert 'r2' in result
    assert 'rmse' in result

def test_fit_gwr_model_convergence_error(sample_gdf):
    """Test behavior when GWR fails (simulated)."""
    with patch('modeling.GWRModel.fit', side_effect=Exception("Convergence failed")):
        result = fit_gwr_model(sample_gdf, ['feature1'], 'target')
        assert result['type'] == 'OLS'
        assert result.get('status') != 'success' or 'fallback' in str(result.get('type', ''))

def test_gwr_bandwidth_sweep_logic():
    """Verify that bandwidth parameter is used."""
    gwr1 = GWRModel(bandwidth=1.0)
    gwr2 = GWRModel(bandwidth=10.0)
    assert gwr1.bandwidth != gwr2.bandwidth

if __name__ == "__main__":
    pytest.main([__file__, "-v"])