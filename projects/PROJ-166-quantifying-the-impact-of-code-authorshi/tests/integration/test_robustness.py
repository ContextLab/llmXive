import pytest
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Mock data for testing
@pytest.fixture
def mock_repo_metrics(tmp_path):
    """Create a mock repo_metrics.csv file."""
    data = {
        'url': ['repo1', 'repo2', 'repo3', 'repo4', 'repo5'],
        'language': ['Python', 'JavaScript', 'Python', 'JavaScript', 'Python'],
        'unique_authors': [10, 20, 15, 25, 12],
        'kloc': [5000, 8000, 6000, 9000, 7000],
        'cve_count': [5, 8, 6, 10, 7],
        'project_age': [5, 3, 4, 2, 6],
        'release_count': [10, 15, 12, 18, 14]
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / 'repo_metrics.csv'
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def mock_author_contributions(tmp_path):
    """Create a mock author_contributions.csv file."""
    data = {
        'url': ['repo1', 'repo1', 'repo2', 'repo2', 'repo3', 'repo3', 'repo4', 'repo4', 'repo5', 'repo5'],
        'author': ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'd1', 'd2', 'e1', 'e2'],
        'lines': [100, 200, 150, 250, 120, 280, 180, 320, 130, 270]
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / 'author_contributions.csv'
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def mock_data_files(mock_repo_metrics, mock_author_contributions, tmp_path):
    """Create necessary directories and files for testing."""
    # Ensure logs directory exists
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Create data/processed directory
    data_processed = tmp_path / 'data' / 'processed'
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Copy mock files to expected locations
    import shutil
    shutil.copy(mock_repo_metrics, data_processed / 'repo_metrics.csv')
    shutil.copy(mock_author_contributions, data_processed / 'author_contributions.csv')
    
    return tmp_path

def test_robustness_results_generation(mock_data_files, tmp_path):
    """Test that robustness analysis generates valid results."""
    # Change to temp directory to avoid modifying real data
    original_dir = os.getcwd()
    os.chdir(mock_data_files)
    
    try:
        # Import and run the main function
        from code.analysis.robustness import main
        results = main()
        
        # Check that results file was created
        output_path = Path('data/processed/robustness_results.json')
        assert output_path.exists(), "Robustness results file not created"
        
        # Load and validate results
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        # Check structure
        assert 'subsample_analysis' in loaded_results, "Missing subsample_analysis"
        assert 'entropy_model' in loaded_results, "Missing entropy_model"
        assert 'metadata' in loaded_results, "Missing metadata"
        
        # Check subsample results
        subsample = loaded_results['subsample_analysis']
        assert len(subsample) > 0, "No subsample results generated"
        
        # Check that at least one language has results
        has_results = False
        for lang, result in subsample.items():
            if result is not None:
                has_results = True
                assert 'coefficients' in result, f"Missing coefficients for {lang}"
                assert 'p_values' in result, f"Missing p_values for {lang}"
                assert 'adjusted_p_values' in result, f"Missing adjusted_p_values for {lang}"
                assert 'convergence_status' in result, f"Missing convergence_status for {lang}"
        
        assert has_results, "No valid subsample results found"
        
        # Check entropy model
        entropy = loaded_results['entropy_model']
        assert entropy is not None, "Entropy model results are None"
        assert 'coefficients' in entropy, "Missing coefficients for entropy model"
        assert 'p_values' in entropy, "Missing p_values for entropy model"
        assert 'adjusted_p_values' in entropy, "Missing adjusted_p_values for entropy model"
        
        # Check metadata
        metadata = loaded_results['metadata']
        assert 'total_repos' in metadata, "Missing total_repos in metadata"
        assert 'languages_analyzed' in metadata, "Missing languages_analyzed in metadata"
        assert 'timestamp' in metadata, "Missing timestamp in metadata"
        
    finally:
        os.chdir(original_dir)

def test_entropy_calculation(mock_data_files, tmp_path):
    """Test that Shannon entropy is calculated correctly."""
    original_dir = os.getcwd()
    os.chdir(mock_data_files)
    
    try:
        from code.analysis.robustness import calculate_shannon_entropy
        
        # Load author contributions
        author_df = pd.read_csv('data/processed/author_contributions.csv')
        
        # Calculate entropy
        entropy_series = calculate_shannon_entropy(author_df)
        
        # Check results
        assert len(entropy_series) > 0, "No entropy values calculated"
        assert all(entropy_series >= 0), "Entropy values should be non-negative"
        
        # Check that entropy values are reasonable (should be > 0 for multiple authors)
        for url, entropy in entropy_series.items():
            assert entropy > 0, f"Entropy should be positive for {url} with multiple authors"
        
    finally:
        os.chdir(original_dir)

def test_zero_kloc_filtering(mock_data_files, tmp_path):
    """Test that rows with zero KLOC are filtered out."""
    original_dir = os.getcwd()
    os.chdir(mock_data_files)
    
    try:
        from code.analysis.robustness import filter_zero_kloc
        
        # Load repo metrics
        df = pd.read_csv('data/processed/repo_metrics.csv')
        
        # Add a row with zero KLOC
        zero_kloc_row = pd.DataFrame({
            'url': ['zero_kloc_repo'],
            'language': ['Python'],
            'unique_authors': [5],
            'kloc': [0],
            'cve_count': [1],
            'project_age': [1],
            'release_count': [1]
        })
        df = pd.concat([df, zero_kloc_row], ignore_index=True)
        
        # Filter
        filtered_df = filter_zero_kloc(df)
        
        # Check that zero KLOC row was removed
        assert len(filtered_df) == len(df) - 1, "Zero KLOC row should be filtered out"
        assert not (filtered_df['kloc'] == 0).any(), "No rows with zero KLOC should remain"
        
    finally:
        os.chdir(original_dir)

def test_benjamini_hochberg_correction(mock_data_files, tmp_path):
    """Test that Benjamini-Hochberg correction is applied correctly."""
    original_dir = os.getcwd()
    os.chdir(mock_data_files)
    
    try:
        from code.analysis.robustness import benjamini_hochberg
        
        # Test with known p-values
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted = benjamini_hochberg(p_values)
        
        # Check that adjusted p-values are non-decreasing
        assert all(adjusted[i] <= adjusted[i+1] for i in range(len(adjusted)-1)), \
            "Adjusted p-values should be non-decreasing"
        
        # Check that adjusted p-values are <= 1
        assert all(p <= 1 for p in adjusted), "Adjusted p-values should be <= 1"
        
        # Check that adjusted p-values are >= original p-values
        assert all(adjusted[i] >= p_values[i] for i in range(len(p_values))), \
            "Adjusted p-values should be >= original p-values"
        
    finally:
        os.chdir(original_dir)