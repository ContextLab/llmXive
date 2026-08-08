"""
Unit tests for preprocessing module.

Tests:
- harmonize_gene_ids
- filter_low_expression_genes
- split_data_stratified
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.preprocessing import (
    harmonize_gene_ids,
    filter_low_expression_genes,
    split_data_stratified,
    load_processed_data,
    save_processed_data
)


class MockMyGeneInfo:
    """Mock MyGeneInfo for testing without external API calls."""

    def __init__(self):
        self.mock_mappings = {
            'ENSG00000139618': 'BRCA2',
            'ENSG00000157764': 'BRAF',
            'ENSG00000141510': 'TP53',
            'ENSG00000171862': 'PTEN',
            'ENSG00000133703': 'KRAS',
            '12345': 'EGFR',  # Entrez ID example
            '67890': 'NOTAPROTEIN'  # Will not map
        }

    def querymany(self, ids, scopes=None, fields=None, species=None, as_dataframe=True):
        """Mock querymany that returns simulated mappings."""
        results = []
        for gene_id in ids:
            symbol = self.mock_mappings.get(gene_id, '')
            results.append({
                'query': gene_id,
                'symbol': symbol if symbol else None
            })

        if as_dataframe:
            return pd.DataFrame(results)
        return results


@pytest.fixture
def sample_counts():
    """Create sample gene expression data for testing."""
    data = {
        'gene_id': ['ENSG00000139618', 'ENSG00000157764', 'ENSG00000141510',
                   'ENSG00000171862', 'ENSG00000133703', '12345', '67890'],
        'sample1': [100, 200, 50, 300, 150, 80, 10],
        'sample2': [120, 180, 60, 280, 140, 90, 5],
        'sample3': [90, 220, 45, 320, 160, 70, 8],
        'sample4': [110, 190, 55, 290, 145, 85, 12],
        'response_label': ['responder', 'responder', 'non_responder',
                          'non_responder', 'responder', 'responder', 'non_responder']
    }
    return pd.DataFrame(data)


class TestFilterLowExpressionGenes:
    """Tests for filter_low_expression_genes function."""

    def test_filter_low_expression_genes(self, sample_counts):
        """Test that low expression genes are filtered correctly."""
        # Create data where gene '67890' has very low expression in all samples
        df_filtered, stats = filter_low_expression_genes(
            sample_counts,
            expression_columns=['sample1', 'sample2', 'sample3', 'sample4'],
            min_cpm=1.0,
            max_low_fraction=0.8
        )

        # Check that the low-expression gene was removed
        assert '67890' not in df_filtered['gene_id'].values
        assert len(df_filtered) < len(sample_counts)
        assert stats['removed_genes'] > 0

    def test_no_filtering_when_all_above_threshold(self, sample_counts):
        """Test that no genes are filtered when all are above threshold."""
        # Increase expression values to be well above threshold
        df_high = sample_counts.copy()
        for col in ['sample1', 'sample2', 'sample3', 'sample4']:
            df_high[col] = df_high[col] * 100

        df_filtered, stats = filter_low_expression_genes(
            df_high,
            expression_columns=['sample1', 'sample2', 'sample3', 'sample4']
        )

        assert len(df_filtered) == len(df_high)
        assert stats['removed_genes'] == 0


class TestSplitDataStratified:
    """Tests for split_data_stratified function."""

    def test_split_data_stratified_balanced(self):
        """Test stratified split with balanced classes."""
        data = {
            'gene_id': [f'gene{i}' for i in range(100)],
            'sample1': np.random.randint(0, 1000, 100),
            'response_label': ['responder'] * 50 + ['non_responder'] * 50
        }
        df = pd.DataFrame(data)

        discovery, training = split_data_stratified(
            df,
            response_column='response_label',
            split_ratio=0.7,
            random_seed=42
        )

        # Check sizes
        assert len(discovery) + len(training) == len(df)
        assert len(discovery) == int(len(df) * 0.7)

        # Check stratification (proportions should be similar)
        discovery_resp_ratio = (discovery['response_label'] == 'responder').mean()
        training_resp_ratio = (training['response_label'] == 'responder').mean()

        assert abs(discovery_resp_ratio - 0.5) < 0.1
        assert abs(training_resp_ratio - 0.5) < 0.1

    def test_split_data_stratified_imbalanced(self):
        """Test stratified split with imbalanced classes."""
        data = {
            'gene_id': [f'gene{i}' for i in range(100)],
            'sample1': np.random.randint(0, 1000, 100),
            'response_label': ['responder'] * 20 + ['non_responder'] * 80
        }
        df = pd.DataFrame(data)

        discovery, training = split_data_stratified(
            df,
            response_column='response_label',
            split_ratio=0.7,
            random_seed=42
        )

        # Check stratification is maintained
        discovery_resp_ratio = (discovery['response_label'] == 'responder').mean()
        training_resp_ratio = (training['response_label'] == 'responder').mean()

        assert abs(discovery_resp_ratio - 0.2) < 0.1
        assert abs(training_resp_ratio - 0.2) < 0.1

    def test_split_data_missing_strata_column(self):
        """Test that missing response column raises error."""
        data = {
            'gene_id': [f'gene{i}' for i in range(10)],
            'sample1': np.random.randint(0, 1000, 10)
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="Response column"):
            split_data_stratified(df, response_column='missing_column')


def test_harmonize_gene_ids(sample_counts):
    """Test gene ID harmonization."""
    # Note: This test uses the mock, but in real execution would call mygene.info
    # For now, we test the structure and error handling

    # Test with missing ID column
    df_no_id = sample_counts.drop(columns=['gene_id'])
    with pytest.raises(ValueError, match="ID column"):
        harmonize_gene_ids(df_no_id, id_column='nonexistent')

    # Test with empty ID column
    df_empty = sample_counts.copy()
    df_empty['gene_id'] = None
    with pytest.raises(ValueError, match="No valid gene IDs"):
        harmonize_gene_ids(df_empty)

    # Test normal operation (would map IDs in real scenario)
    # Here we just verify the function signature and basic behavior
    df_harmonized, stats = harmonize_gene_ids(
        sample_counts,
        id_column='gene_id',
        output_column='gene_symbol'
    )

    assert 'gene_symbol' in df_harmonized.columns
    assert 'mapped_count' in stats
    assert 'coverage' in stats


def test_load_processed_data(tmp_path):
    """Test loading processed data."""
    # Create a temporary CSV file
    data = {'gene_id': ['A', 'B'], 'sample1': [100, 200]}
    df = pd.DataFrame(data)
    test_file = tmp_path / 'test.csv'
    df.to_csv(test_file, index=False)

    loaded_df = load_processed_data(str(test_file))
    assert len(loaded_df) == 2
    assert 'gene_id' in loaded_df.columns

    # Test missing file
    with pytest.raises(FileNotFoundError):
        load_processed_data('/nonexistent/file.csv')


def test_save_processed_data(tmp_path):
    """Test saving processed data."""
    data = {'gene_id': ['A', 'B'], 'sample1': [100, 200]}
    df = pd.DataFrame(data)
    output_file = tmp_path / 'output.csv'

    save_processed_data(df, str(output_file))
    assert output_file.exists()

    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 2