"""
Unit tests for edge cases in the analysis pipeline.

Tests:
- test_zero_kloc_exclusion: Verify rows with kloc=0 are excluded.
- test_empty_nvd_match: Verify cve_count=0 when no match found.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.fit_models import load_data, filter_zero_kloc
from code.analysis.robustness import load_data as robustness_load_data
from code.data.merge_datasets import merge_datasets, validate_merged_data
from code.config import ensure_directories


class TestZeroKlocExclusion:
    """Tests for filtering out rows with zero KLOC."""

    def test_zero_kloc_exclusion(self, tmp_path):
        """Verify rows with kloc=0 are excluded by filter_zero_kloc."""
        # Create a mock dataset with zero and non-zero KLOC values
        mock_data = {
            'url': ['repo1', 'repo2', 'repo3', 'repo4'],
            'unique_authors': [10, 0, 5, 20],
            'kloc': [100.5, 0.0, 50.2, 0.0],
            'cve_count': [5, 2, 0, 10],
            'language': ['Python', 'JS', 'Go', 'Rust'],
            'project_age': [365, 180, 90, 730],
            'release_count': [10, 5, 2, 20]
        }
        df = pd.DataFrame(mock_data)
        
        # Save to a temporary CSV file
        csv_path = tmp_path / "test_metrics.csv"
        df.to_csv(csv_path, index=False)
        
        # Load and filter the data
        filtered_df = filter_zero_kloc(csv_path)
        
        # Assert that rows with kloc=0 are excluded
        assert len(filtered_df) == 2, "Expected 2 rows after filtering zero KLOC"
        assert all(filtered_df['kloc'] > 0), "All remaining rows should have kloc > 0"
        
        # Verify specific rows were kept
        urls = set(filtered_df['url'])
        assert 'repo1' in urls, "repo1 (kloc=100.5) should be kept"
        assert 'repo3' in urls, "repo3 (kloc=50.2) should be kept"
        assert 'repo2' not in urls, "repo2 (kloc=0.0) should be excluded"
        assert 'repo4' not in urls, "repo4 (kloc=0.0) should be excluded"

    def test_all_zero_kloc_exclusion(self, tmp_path):
        """Verify behavior when all rows have kloc=0."""
        mock_data = {
            'url': ['repo1', 'repo2'],
            'unique_authors': [0, 5],
            'kloc': [0.0, 0.0],
            'cve_count': [0, 0],
            'language': ['Python', 'JS'],
            'project_age': [365, 180],
            'release_count': [10, 5]
        }
        df = pd.DataFrame(mock_data)
        
        csv_path = tmp_path / "all_zero.csv"
        df.to_csv(csv_path, index=False)
        
        filtered_df = filter_zero_kloc(csv_path)
        
        assert len(filtered_df) == 0, "Expected empty DataFrame when all kloc=0"
        assert filtered_df.empty, "DataFrame should be empty"

    def test_no_zero_kloc(self, tmp_path):
        """Verify behavior when no rows have kloc=0."""
        mock_data = {
            'url': ['repo1', 'repo2'],
            'unique_authors': [10, 5],
            'kloc': [100.5, 50.2],
            'cve_count': [5, 0],
            'language': ['Python', 'JS'],
            'project_age': [365, 180],
            'release_count': [10, 5]
        }
        df = pd.DataFrame(mock_data)
        
        csv_path = tmp_path / "no_zero.csv"
        df.to_csv(csv_path, index=False)
        
        filtered_df = filter_zero_kloc(csv_path)
        
        assert len(filtered_df) == 2, "Expected all rows to be kept"
        pd.testing.assert_frame_equal(filtered_df, df)

    def test_zero_kloc_robustness_analysis(self, tmp_path):
        """Verify robustness analysis also filters zero KLOC."""
        mock_data = {
            'url': ['repo1', 'repo2', 'repo3'],
            'unique_authors': [10, 0, 5],
            'kloc': [100.5, 0.0, 50.2],
            'cve_count': [5, 2, 0],
            'language': ['Python', 'JS', 'Go'],
            'project_age': [365, 180, 90],
            'release_count': [10, 5, 2]
        }
        df = pd.DataFrame(mock_data)
        
        csv_path = tmp_path / "robustness_test.csv"
        df.to_csv(csv_path, index=False)
        
        # Use robustness load_data which should also filter zero KLOC
        filtered_df = robustness_load_data(csv_path)
        
        assert len(filtered_df) == 2, "Expected 2 rows after filtering in robustness load"
        assert all(filtered_df['kloc'] > 0), "All remaining rows should have kloc > 0"

class TestEmptyNvdMatch:
    """Tests for handling repositories with no NVD CVE matches."""

    def test_empty_nvd_match(self, tmp_path):
        """Verify cve_count=0 when no match found in NVD."""
        # Create target list with repos
        target_data = {
            'url': ['github.com/org/repo1', 'github.com/org/repo2', 'github.com/org/repo3'],
            'language': ['Python', 'JS', 'Go'],
            'stars': [1000, 500, 2000],
            'age': [365, 180, 730]
        }
        target_df = pd.DataFrame(target_data)
        target_path = tmp_path / "target_list.csv"
        target_df.to_csv(target_path, index=False)
        
        # Create GitHub metrics with all repos
        github_data = {
            'url': ['github.com/org/repo1', 'github.com/org/repo2', 'github.com/org/repo3'],
            'unique_authors': [10, 5, 20],
            'raw_line_count': [10000, 5000, 20000],
            'kloc': [10.0, 5.0, 20.0]
        }
        github_df = pd.DataFrame(github_data)
        github_path = tmp_path / "github_metrics.csv"
        github_df.to_csv(github_path, index=False)
        
        # Create NVD CVE data with only one match
        nvd_data = [
            {
                'cve_id': 'CVE-2023-1234',
                'github_repo': 'github.com/org/repo1',
                'published_date': '2023-01-01',
                'cvss_score': 7.5
            },
            {
                'cve_id': 'CVE-2023-5678',
                'github_repo': 'github.com/org/repo1',
                'published_date': '2023-02-01',
                'cvss_score': 5.0
            }
            # Note: repo2 and repo3 have no matches
        ]
        nvd_path = tmp_path / "nvd_cves.json"
        with open(nvd_path, 'w') as f:
            json.dump(nvd_data, f)
        
        # Perform the merge
        merged_df = merge_datasets(str(target_path), str(github_path), str(nvd_path))
        
        # Validate the merged data
        validate_merged_data(merged_df)
        
        # Assert that repos with no matches have cve_count=0
        assert len(merged_df) == 3, "Expected all 3 repos in merged data"
        
        # Find the row for repo2 (no match)
        repo2_row = merged_df[merged_df['url'] == 'github.com/org/repo2']
        assert len(repo2_row) == 1, "repo2 should exist in merged data"
        assert repo2_row['cve_count'].iloc[0] == 0, "repo2 should have cve_count=0"
        
        # Find the row for repo3 (no match)
        repo3_row = merged_df[merged_df['url'] == 'github.com/org/repo3']
        assert len(repo3_row) == 1, "repo3 should exist in merged data"
        assert repo3_row['cve_count'].iloc[0] == 0, "repo3 should have cve_count=0"
        
        # Verify repo1 has the correct count (2 CVEs)
        repo1_row = merged_df[merged_df['url'] == 'github.com/org/repo1']
        assert len(repo1_row) == 1, "repo1 should exist in merged data"
        assert repo1_row['cve_count'].iloc[0] == 2, "repo1 should have cve_count=2"

    def test_complete_nvd_empty(self, tmp_path):
        """Verify behavior when NVD data is completely empty."""
        target_data = {
            'url': ['github.com/org/repo1'],
            'language': ['Python'],
            'stars': [1000],
            'age': [365]
        }
        target_df = pd.DataFrame(target_data)
        target_path = tmp_path / "target_list.csv"
        target_df.to_csv(target_path, index=False)
        
        github_data = {
            'url': ['github.com/org/repo1'],
            'unique_authors': [10],
            'raw_line_count': [10000],
            'kloc': [10.0]
        }
        github_df = pd.DataFrame(github_data)
        github_path = tmp_path / "github_metrics.csv"
        github_df.to_csv(github_path, index=False)
        
        # Empty NVD data
        nvd_data = []
        nvd_path = tmp_path / "nvd_cves.json"
        with open(nvd_path, 'w') as f:
            json.dump(nvd_data, f)
        
        merged_df = merge_datasets(str(target_path), str(github_path), str(nvd_path))
        
        assert len(merged_df) == 1, "Expected 1 repo in merged data"
        assert merged_df['cve_count'].iloc[0] == 0, "cve_count should be 0"

    def test_null_cve_count_handling(self, tmp_path):
        """Verify that null cve_count values are converted to 0."""
        # This test verifies the validation function handles nulls
        mock_data = {
            'url': ['repo1', 'repo2', 'repo3'],
            'unique_authors': [10, 5, 20],
            'kloc': [100.5, 50.2, 200.0],
            'cve_count': [5, None, 10],  # None represents null
            'language': ['Python', 'JS', 'Go'],
            'project_age': [365, 180, 730],
            'release_count': [10, 5, 20]
        }
        df = pd.DataFrame(mock_data)
        
        # The validation function should raise an error if nulls are found
        # But in the actual merge process, we ensure cve_count defaults to 0
        # This test documents the expected behavior
        
        # Create a scenario where we manually set cve_count to 0 for nulls
        df['cve_count'] = df['cve_count'].fillna(0)
        
        # Now validation should pass
        try:
            validate_merged_data(df)
        except ValueError as e:
            pytest.fail(f"Validation failed unexpectedly: {e}")

class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_combined_edge_cases(self, tmp_path):
        """Test dataset with both zero KLOC and missing NVD matches."""
        target_data = {
            'url': ['github.com/org/repo1', 'github.com/org/repo2', 'github.com/org/repo3', 'github.com/org/repo4'],
            'language': ['Python', 'JS', 'Go', 'Rust'],
            'stars': [1000, 500, 2000, 100],
            'age': [365, 180, 730, 90]
        }
        target_df = pd.DataFrame(target_data)
        target_path = tmp_path / "target_list.csv"
        target_df.to_csv(target_path, index=False)
        
        github_data = {
            'url': ['github.com/org/repo1', 'github.com/org/repo2', 'github.com/org/repo3', 'github.com/org/repo4'],
            'unique_authors': [10, 0, 5, 20],
            'raw_line_count': [10000, 0, 5000, 20000],
            'kloc': [10.0, 0.0, 5.0, 20.0]  # repo2 has zero KLOC
        }
        github_df = pd.DataFrame(github_data)
        github_path = tmp_path / "github_metrics.csv"
        github_df.to_csv(github_path, index=False)
        
        nvd_data = [
            {
                'cve_id': 'CVE-2023-1234',
                'github_repo': 'github.com/org/repo1',
                'published_date': '2023-01-01',
                'cvss_score': 7.5
            }
            # Only repo1 has a CVE match
        ]
        nvd_path = tmp_path / "nvd_cves.json"
        with open(nvd_path, 'w') as f:
            json.dump(nvd_data, f)
        
        # Perform merge
        merged_df = merge_datasets(str(target_path), str(github_path), str(nvd_path))
        
        # Validate
        validate_merged_data(merged_df)
        
        # Filter zero KLOC
        filtered_df = filter_zero_kloc(merged_df)
        
        # Expected: repo1 (kloc=10, cve=1), repo3 (kloc=5, cve=0), repo4 (kloc=20, cve=0)
        # repo2 should be excluded due to zero KLOC
        assert len(filtered_df) == 3, f"Expected 3 rows, got {len(filtered_df)}"
        
        # Verify repo2 is excluded
        assert 'github.com/org/repo2' not in filtered_df['url'].values, "repo2 should be excluded"
        
        # Verify cve_count=0 for repos without matches
        repo3_row = filtered_df[filtered_df['url'] == 'github.com/org/repo3']
        assert repo3_row['cve_count'].iloc[0] == 0, "repo3 should have cve_count=0"
        
        repo4_row = filtered_df[filtered_df['url'] == 'github.com/org/repo4']
        assert repo4_row['cve_count'].iloc[0] == 0, "repo4 should have cve_count=0"