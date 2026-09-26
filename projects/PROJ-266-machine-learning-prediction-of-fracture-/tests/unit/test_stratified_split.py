import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.preprocess import perform_stratified_split, generate_split_metadata_csv
from code.utils.config import get_config_dict

def test_stratified_split_basic():
    """Test basic stratified split functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test metadata
        data = [
            {"image_path": "img1.png", "alloy_family": "steel", "k_ic": 50.0},
            {"image_path": "img2.png", "alloy_family": "steel", "k_ic": 52.0},
            {"image_path": "img3.png", "alloy_family": "steel", "k_ic": 48.0},
            {"image_path": "img4.png", "alloy_family": "Al", "k_ic": 30.0},
            {"image_path": "img5.png", "alloy_family": "Al", "k_ic": 32.0},
            {"image_path": "img6.png", "alloy_family": "Al", "k_ic": 28.0},
            {"image_path": "img7.png", "alloy_family": "Ti", "k_ic": 80.0},
            {"image_path": "img8.png", "alloy_family": "Ti", "k_ic": 82.0},
            {"image_path": "img9.png", "alloy_family": "Ti", "k_ic": 78.0},
        ]
        
        metadata_path = tmpdir / "metadata.json"
        output_path = tmpdir / "split.csv"
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f)
        
        config = get_config_dict()
        perform_stratified_split(metadata_path, output_path, config)
        
        # Verify output
        assert output_path.exists()
        df = pd.read_csv(output_path)
        
        assert set(df['split'].unique()) == {'train', 'val', 'test'}
        assert set(df['alloy_family'].unique()) == {'steel', 'Al', 'Ti'}
        
        # Check proportions approximately
        train_count = len(df[df['split'] == 'train'])
        total = len(df)
        assert 0.65 * total < train_count < 0.75 * total, "Train split should be ~70%"

def test_stratified_split_minimum_samples():
    """Test that split fails if a family has too few samples."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create metadata with only 2 steel samples
        data = [
            {"image_path": "img1.png", "alloy_family": "steel", "k_ic": 50.0},
            {"image_path": "img2.png", "alloy_family": "steel", "k_ic": 52.0},
            {"image_path": "img3.png", "alloy_family": "Al", "k_ic": 30.0},
            {"image_path": "img4.png", "alloy_family": "Al", "k_ic": 32.0},
            {"image_path": "img5.png", "alloy_family": "Al", "k_ic": 28.0},
            {"image_path": "img6.png", "alloy_family": "Ti", "k_ic": 80.0},
            {"image_path": "img7.png", "alloy_family": "Ti", "k_ic": 82.0},
            {"image_path": "img8.png", "alloy_family": "Ti", "k_ic": 78.0},
        ]
        
        metadata_path = tmpdir / "metadata.json"
        output_path = tmpdir / "split.csv"
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f)
        
        config = get_config_dict()
        
        with pytest.raises(ValueError, match="Insufficient samples"):
            perform_stratified_split(metadata_path, output_path, config)

def test_stratified_split_test_set_completeness():
    """Test that split fails if test set would miss a family."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create metadata with only 1 sample per family (too few for test set)
        data = [
            {"image_path": "img1.png", "alloy_family": "steel", "k_ic": 50.0},
            {"image_path": "img2.png", "alloy_family": "Al", "k_ic": 30.0},
            {"image_path": "img3.png", "alloy_family": "Ti", "k_ic": 80.0},
        ]
        
        metadata_path = tmpdir / "metadata.json"
        output_path = tmpdir / "split.csv"
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f)
        
        config = get_config_dict()
        
        with pytest.raises(ValueError, match="Insufficient samples"):
            perform_stratified_split(metadata_path, output_path, config)

def test_generate_split_metadata_csv():
    """Test generation of split metadata summary CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create sample split data
        data = {
            'split': ['train', 'train', 'val', 'test', 'test'],
            'alloy_family': ['steel', 'Al', 'steel', 'Al', 'Ti'],
            'k_ic': [50.0, 30.0, 52.0, 32.0, 80.0]
        }
        df = pd.DataFrame(data)
        
        output_path = tmpdir / "summary.csv"
        generate_split_metadata_csv(df, output_path)
        
        assert output_path.exists()
        summary_df = pd.read_csv(output_path)
        
        assert list(summary_df.columns) == ['split', 'alloy_family', 'count']
        assert summary_df['count'].sum() == len(data['split'])