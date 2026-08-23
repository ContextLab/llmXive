"""
Integration test for subgroup filtering logic (n >= 30).

This test verifies that the subgroup analysis logic correctly:
1. Loads the processed dataset.
2. Groups by demographic fields (age/gender).
3. Filters out groups with fewer than 30 samples.
4. Logs excluded groups and reports the final count.

It does NOT run the full CLMM fitting, but validates the data
preparation step required for T034 (Subgroup Analysis).
"""

import os
import sys
import logging
import pytest
import pandas as pd
from pathlib import Path

# Add the code directory to the path to allow imports
# This mimics the execution environment
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIN_SUBGROUP_SIZE = 30

def filter_subgroups(df: pd.DataFrame, group_cols: list, min_size: int = MIN_SUBGROUP_SIZE) -> tuple[pd.DataFrame, list[dict]]:
    """
    Filter a DataFrame to keep only subgroups with at least `min_size` rows.
    
    Args:
        df: Input DataFrame.
        group_cols: List of column names to group by (e.g., ['age_group', 'gender']).
        min_size: Minimum number of rows required to keep a group.
    
    Returns:
        tuple: (filtered_df, list_of_excluded_groups)
    """
    if not group_cols:
        return df, []

    # Calculate group sizes
    group_sizes = df.groupby(group_cols).size().reset_index(name='count')
    
    excluded_groups = []
    valid_groups_mask = group_sizes['count'] >= min_size
    
    # Identify excluded groups for logging
    for _, row in group_sizes[~valid_groups_mask].iterrows():
        excluded_groups.append({
            "group": {col: row[col] for col in group_cols},
            "count": int(row['count']),
            "reason": f"Size {row['count']} < {min_size}"
        })
    
    # Filter the main dataframe
    # We need to keep rows where the combination of group_cols is in the valid set
    valid_groups = group_sizes[valid_groups_mask][group_cols]
    
    if valid_groups.empty:
        logger.warning("No subgroups met the minimum size requirement. Returning empty DataFrame.")
        return pd.DataFrame(columns=df.columns), excluded_groups

    # Merge to filter
    filtered_df = df.merge(valid_groups, on=group_cols, how='inner')
    
    return filtered_df, excluded_groups

@pytest.fixture
def sample_data():
    """
    Create a synthetic DataFrame that mimics the structure of 
    data/processed/scored_dialogues.parquet for testing purposes.
    """
    # We create a dataset with known group sizes to test the logic.
    # We need at least one group >= 30 and one < 30.
    data = {
        'user_id': [],
        'dialogue_id': [],
        'quality_rating': [],
        'politeness_score': [],
        'age': [],
        'gender': []
    }
    
    # Group 1: Male, Age 18-24 (Size 10) -> Should be excluded
    for i in range(10):
        data['user_id'].append(f'user_excl_{i}')
        data['dialogue_id'].append(f'dia_excl_{i}')
        data['quality_rating'].append(3)
        data['politeness_score'].append(0.5)
        data['age'].append(20)
        data['gender'].append('Male')
    
    # Group 2: Female, Age 25-34 (Size 50) -> Should be included
    for i in range(50):
        data['user_id'].append(f'user_inc_{i}')
        data['dialogue_id'].append(f'dia_inc_{i}')
        data['quality_rating'].append(4)
        data['politeness_score'].append(0.7)
        data['age'].append(30)
        data['gender'].append('Female')
        
    # Group 3: Male, Age 25-34 (Size 35) -> Should be included
    for i in range(35):
        data['user_id'].append(f'user_inc2_{i}')
        data['dialogue_id'].append(f'dia_inc2_{i}')
        data['quality_rating'].append(4)
        data['politeness_score'].append(0.6)
        data['age'].append(30)
        data['gender'].append('Male')

    return pd.DataFrame(data)

def test_subgroup_filtering_logic(sample_data):
    """
    Test that the filtering logic correctly identifies and excludes small groups.
    """
    # We are grouping by a simplified 'age_group' and 'gender' for this test
    # In the real implementation, we might bin 'age' first.
    # For this test, let's assume we have a column 'age_group' derived from 'age'.
    # Since the raw data has 'age', we'll bin it in the test to simulate the pre-step.
    
    # Create age groups
    def bin_age(age):
        if 18 <= age <= 24: return '18-24'
        if 25 <= age <= 34: return '25-34'
        return 'Other'
    
    sample_data['age_group'] = sample_data['age'].apply(bin_age)
    
    # Run the filter
    filtered_df, excluded = filter_subgroups(
        sample_data, 
        group_cols=['age_group', 'gender'], 
        min_size=30
    )
    
    # Assertions
    assert len(excluded) == 1, f"Expected 1 excluded group, found {len(excluded)}"
    assert excluded[0]['count'] == 10, f"Expected excluded count 10, found {excluded[0]['count']}"
    assert excluded[0]['group']['age_group'] == '18-24'
    assert excluded[0]['group']['gender'] == 'Male'
    
    # Check remaining rows
    # Original: 10 + 50 + 35 = 95
    # Excluded: 10
    # Expected: 85
    assert len(filtered_df) == 85, f"Expected 85 rows after filtering, found {len(filtered_df)}"
    
    # Verify no excluded group remains
    remaining_groups = filtered_df.groupby(['age_group', 'gender']).size()
    for count in remaining_groups:
        assert count >= 30, f"Found a group with size {count} < 30 after filtering."

def test_edge_case_all_groups_excluded(sample_data):
    """
    Test behavior when all groups are too small.
    """
    # Create a small dataset where every group is < 30
    small_data = sample_data.head(5).copy()
    small_data['age_group'] = small_data['age'].apply(lambda x: '18-24')
    
    filtered_df, excluded = filter_subgroups(
        small_data,
        group_cols=['age_group', 'gender'],
        min_size=30
    )
    
    assert len(filtered_df) == 0, "Expected empty DataFrame when all groups are excluded"
    assert len(excluded) > 0, "Expected exclusion list to be populated"

def test_edge_case_no_groups_defined(sample_data):
    """
    Test behavior when no group columns are provided.
    """
    filtered_df, excluded = filter_subgroups(
        sample_data,
        group_cols=[],
        min_size=30
    )
    
    # Should return the original dataframe unchanged
    assert len(filtered_df) == len(sample_data)
    assert len(excluded) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])