import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from code.data.merge_datasets import merge_datasets, count_cves_per_repo

def test_url_matching():
    """Mock NVD data, assert exact match logic works and ambiguous matches are ignored."""
    # Create mock target list (GitHub metrics)
    github_data = pd.DataFrame({
        'url': ['https://github.com/org/repoA', 'https://github.com/org/repoB', 'https://github.com/org/repoC'],
        'language': ['Python', 'JavaScript', 'Java'],
        'unique_authors': [10, 5, 20],
        'kloc': [100, 50, 200]
    })

    # Create mock NVD data with exact and ambiguous matches
    nvd_data = pd.DataFrame({
        'cve_id': ['CVE-2023-001', 'CVE-2023-002', 'CVE-2023-003'],
        'url': [
            'https://github.com/org/repoA',  # Exact match
            'https://github.com/org/repoAB', # Ambiguous (substring)
            'https://github.com/org/repoD'   # No match in target
        ],
        'severity': ['HIGH', 'MEDIUM', 'LOW']
    })

    # Mock the loading functions
    with patch('code.data.merge_datasets.load_target_list', return_value=github_data), \
         patch('code.data.merge_datasets.load_nvd_cves', return_value=nvd_data):
        
        result = merge_datasets()
        
        # Verify exact match: repoA should have cve_count = 1
        repoA_row = result[result['url'] == 'https://github.com/org/repoA']
        assert len(repoA_row) == 1, "repoA should exist in result"
        assert repoA_row.iloc[0]['cve_count'] == 1, "repoA should have exactly 1 CVE (exact match)"
        
        # Verify ambiguous match: repoB should have cve_count = 0 (no exact match)
        repoB_row = result[result['url'] == 'https://github.com/org/repoB']
        assert len(repoB_row) == 1, "repoB should exist in result"
        assert repoB_row.iloc[0]['cve_count'] == 0, "repoB should have 0 CVEs (ambiguous match ignored)"
        
        # Verify no match: repoC should have cve_count = 0
        repoC_row = result[result['url'] == 'https://github.com/org/repoC']
        assert len(repoC_row) == 1, "repoC should exist in result"
        assert repoC_row.iloc[0]['cve_count'] == 0, "repoC should have 0 CVEs"

def test_count_cves_per_repo_exact_matching():
    """Test that count_cves_per_repo only counts exact URL matches."""
    nvd_data = pd.DataFrame({
        'cve_id': ['CVE-1', 'CVE-2', 'CVE-3'],
        'url': [
            'https://github.com/org/repo',
            'https://github.com/org/repoX',  # Should not match
            'https://github.com/org/repo'    # Exact match again
        ]
    })
    
    target_url = 'https://github.com/org/repo'
    count = count_cves_per_repo(nvd_data, target_url)
    
    assert count == 2, f"Expected 2 exact matches, got {count}"

def test_count_cves_per_repo_no_match():
    """Test that count_cves_per_repo returns 0 when no match exists."""
    nvd_data = pd.DataFrame({
        'cve_id': ['CVE-1'],
        'url': ['https://github.com/org/other']
    })
    
    target_url = 'https://github.com/org/repo'
    count = count_cves_per_repo(nvd_data, target_url)
    
    assert count == 0, f"Expected 0 matches, got {count}"
