import os
import pandas as pd
import numpy as np
import tempfile
import shutil
import pytest

# Mock the pipeline module to test logic without full pipeline
from src.pipelines.preprocess import calculate_diversity_metrics

@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_diversity_calculation(temp_data_dir):
    # Create synthetic ASV table (Real data requirement applies to end-to-end, 
    # but unit/integration logic verification needs inputs)
    samples = [f'sample_{i}' for i in range(10)]
    asvs = [f'ASV_{i}' for i in range(5)]
    data = np.random.randint(0, 100, size=(10, 5))
    asv_df = pd.DataFrame(data, index=samples, columns=asvs)
    
    asv_path = os.path.join(temp_data_dir, 'asv_table.tsv')
    asv_df.to_csv(asv_path, sep='\t')

    # Create synthetic metadata
    meta_df = pd.DataFrame({
        'ph': np.random.uniform(5, 8, 10),
        'nutrients': np.random.uniform(0, 10, 10)
    }, index=samples)
    
    meta_path = os.path.join(temp_data_dir, 'cleaned_metadata.csv')
    meta_df.to_csv(meta_path)

    output_dir = os.path.join(temp_data_dir, 'output')

    # Run the function
    alpha, bray, eucl = calculate_diversity_metrics(asv_path, meta_path, output_dir)

    # Assertions
    assert os.path.exists(os.path.join(output_dir, 'alpha_diversity.csv'))
    assert os.path.exists(os.path.join(output_dir, 'beta_diversity_bray_curtis.csv'))
    assert os.path.exists(os.path.join(output_dir, 'beta_diversity_euclidean.csv'))
    
    assert 'shannon' in alpha.columns
    assert 'observed_asvs' in alpha.columns
    assert len(alpha) == 10
    
    assert bray.shape == (10, 10)
    assert eucl.shape == (10, 10)
    assert np.allclose(bray.values, bray.values.T) # Symmetry check
    assert np.allclose(eucl.values, eucl.values.T) # Symmetry check
    assert np.all(np.diag(bray.values) == 0) # Diagonal zero check
    assert np.all(np.diag(eucl.values) == 0) # Diagonal zero check
