import pandas as pd
import pytest
from data.merge_datasets import merge_datasets

def test_url_matching():
    """
    Test that exact URL matching works correctly and ambiguous matches are ignored.
    Mock NVD data and target list, then assert exact match logic.
    """
    # Mock target list
    target_list = pd.DataFrame({
        'url': ['https://github.com/org/repo1', 'https://github.com/org/repo2', 'https://github.com/org/repo3'],
        'primary_language': ['Python', 'JavaScript', 'Java'],
        'unique_authors': [10, 20, 30],
        'kloc': [1.5, 2.5, 3.5]
    })

    # Mock NVD CVE data (with exact and ambiguous matches)
    nvd_data = pd.DataFrame({
        'url': ['https://github.com/org/repo1', 'https://github.com/org/repo11', 'https://github.com/org/repo2'],
        'cve_count': [5, 3, 2]
    })

    # Expected result:
    # - repo1: exact match -> cve_count = 5
    # - repo2: exact match -> cve_count = 2
    # - repo3: no match -> cve_count = 0
    # - repo11: ambiguous (substring) -> should be ignored (not merged)

    merged_df = merge_datasets(target_list, nvd_data)

    # Assert exact matches are present
    assert merged_df.loc[merged_df['url'] == 'https://github.com/org/repo1', 'cve_count'].values[0] == 5
    assert merged_df.loc[merged_df['url'] == 'https://github.com/org/repo2', 'cve_count'].values[0] == 2

    # Assert no match gets cve_count = 0
    assert merged_df.loc[merged_df['url'] == 'https://github.com/org/repo3', 'cve_count'].values[0] == 0

    # Assert ambiguous match (repo11) is not in the merged dataframe
    assert 'https://github.com/org/repo11' not in merged_df['url'].values

    # Assert the number of rows is the same as the target list (no new rows added)
    assert len(merged_df) == len(target_list)