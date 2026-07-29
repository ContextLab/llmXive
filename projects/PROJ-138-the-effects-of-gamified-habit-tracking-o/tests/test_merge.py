"""
Tests for the merge functionality (Task T017).
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.merge import merge_datasets, REQUIRED_COLUMNS


@pytest.fixture
def sample_data(tmp_path):
    """Create sample data files for testing."""
    # Create temporary directories
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create sample aggregated data
    agg_data = pd.DataFrame({
        'User_ID': [1, 2, 3, 4, 5],
        'week_number': [1, 1, 1, 2, 2],
        'weekly_adherence_flag': [1, 0, 1, 1, 0]
    })
    agg_path = data_dir / "weekly_aggregates.csv"
    agg_data.to_csv(agg_path, index=False)
    
    # Create sample user traits
    traits_data = pd.DataFrame({
        'User_ID': [1, 2, 3, 4, 5],
        'gamified_status': [True, False, True, False, True],
        'conscientiousness_score': [0.8, 0.3, 0.7, 0.2, 0.9],
        'need_for_achievement': [0.7, 0.4, 0.6, 0.3, 0.8]
    })
    traits_path = data_dir / "user_traits.csv"
    traits_data.to_csv(traits_path, index=False)
    
    return {
        'tmp_path': tmp_path,
        'agg_path': str(agg_path),
        'traits_path': str(traits_path)
    }


def test_merge_with_need_for_achievement(sample_data):
    """Test merge when need_for_achievement column exists."""
    # Change to temp directory to simulate file system
    original_cwd = os.getcwd()
    os.chdir(sample_data['tmp_path'])
    
    try:
        # Mock the file paths by creating symlinks or copying
        processed_dir = Path("data") / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files to expected locations
        shutil.copy(sample_data['agg_path'], processed_dir / "weekly_aggregates.csv")
        shutil.copy(sample_data['traits_path'], processed_dir / "user_traits.csv")
        
        # Run merge
        result = merge_datasets()
        
        # Verify required columns
        for col in REQUIRED_COLUMNS:
            assert col in result.columns, f"Missing required column: {col}"
        
        # Verify need_for_achievement is included
        assert 'need_for_achievement' in result.columns, "need_for_achievement should be included"
        
        # Verify row count
        assert len(result) == 10, f"Expected 10 rows, got {len(result)}"
        
    finally:
        os.chdir(original_cwd)


def test_merge_without_need_for_achievement(sample_data):
    """Test merge when need_for_achievement column does not exist."""
    original_cwd = os.getcwd()
    os.chdir(sample_data['tmp_path'])
    
    try:
        processed_dir = Path("data") / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create aggregated data
        agg_data = pd.read_csv(sample_data['agg_path'])
        agg_data.to_csv(processed_dir / "weekly_aggregates.csv", index=False)
        
        # Create traits data without need_for_achievement
        traits_data = pd.read_csv(sample_data['traits_path'])
        traits_data = traits_data.drop(columns=['need_for_achievement'])
        traits_data.to_csv(processed_dir / "user_traits.csv", index=False)
        
        # Run merge
        result = merge_datasets()
        
        # Verify required columns
        for col in REQUIRED_COLUMNS:
            assert col in result.columns, f"Missing required column: {col}"
        
        # Verify need_for_achievement is NOT included
        assert 'need_for_achievement' not in result.columns, "need_for_achievement should not be included"
        
    finally:
        os.chdir(original_cwd)


def test_merge_missing_aggregated_data(sample_data):
    """Test merge when aggregated data is missing."""
    original_cwd = os.getcwd()
    os.chdir(sample_data['tmp_path'])
    
    try:
        processed_dir = Path("data") / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy only traits data
        shutil.copy(sample_data['traits_path'], processed_dir / "user_traits.csv")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            merge_datasets()
            
    finally:
        os.chdir(original_cwd)


def test_merge_missing_traits_data(sample_data):
    """Test merge when traits data is missing."""
    original_cwd = os.getcwd()
    os.chdir(sample_data['tmp_path'])
    
    try:
        processed_dir = Path("data") / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy only aggregated data
        shutil.copy(sample_data['agg_path'], processed_dir / "weekly_aggregates.csv")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            merge_datasets()
            
    finally:
        os.chdir(original_cwd)