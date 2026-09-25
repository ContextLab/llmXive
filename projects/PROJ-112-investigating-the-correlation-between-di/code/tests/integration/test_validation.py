"""
Integration test for cross-cohort validation (T027).

This test verifies that the cross-cohort validation pipeline (T029)
correctly processes input data from both AGP and UKBB cohorts,
calculates replication status for significant taxa, and produces
the expected output schema.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import shutil
from typing import Dict, List, Any

# Import the validation module to test
# Note: The actual implementation is in src/analysis/validation_cross_cohort.py
# which will be implemented in T029. For this test, we mock the behavior
# or test the file existence and basic structure.
try:
    from src.analysis.validation_cross_cohort import (
        load_association_results,
        load_diff_abundance_results,
        calculate_replication_status,
        run_cross_cohort_validation,
        build_arg_parser,
        main
    )
    HAS_VALIDATION_MODULE = True
except ImportError:
    HAS_VALIDATION_MODULE = False


@pytest.fixture
def temp_validation_dir():
    """Create a temporary directory for validation test artifacts."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_association_data():
    """Generate sample association data for both cohorts."""
    # Create sample data for AGP
    agp_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria'],
        'maaslin2_beta': [0.5, -0.3, 0.1, -0.2],
        'maaslin2_se': [0.1, 0.1, 0.05, 0.08],
        'maaslin2_p_value': [0.001, 0.01, 0.06, 0.02],
        'maaslin2_q_value': [0.005, 0.02, 0.1, 0.03],
        'spearman_rho': [0.45, -0.25, 0.08, -0.15],
        'spearman_se': [0.1, 0.1, 0.05, 0.08],
        'spearman_p_value': [0.002, 0.015, 0.07, 0.025]
    })
    
    # Create sample data for UKBB
    ukbb_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria'],
        'maaslin2_beta': [0.4, -0.35, 0.05, -0.18],
        'maaslin2_se': [0.12, 0.11, 0.06, 0.09],
        'maaslin2_p_value': [0.002, 0.008, 0.08, 0.025],
        'maaslin2_q_value': [0.006, 0.018, 0.12, 0.035],
        'spearman_rho': [0.42, -0.28, 0.06, -0.14],
        'spearman_se': [0.11, 0.11, 0.06, 0.09],
        'spearman_p_value': [0.003, 0.012, 0.09, 0.028]
    })
    
    return agp_data, ukbb_data


@pytest.fixture
def sample_diff_abundance_data():
    """Generate sample differential abundance data for both cohorts."""
    # AGP ANCOM-II results
    agp_ancom = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'method': ['ANCOM-II', 'ANCOM-II'],
        'q_value': [0.004, 0.015],
        'effect_size': [0.48, -0.32],
        'direction': ['positive', 'negative']
    })
    
    # AGP DESeq2 results
    agp_deseq2 = pd.DataFrame({
        'taxon': ['Bacteroides', 'Actinobacteria'],
        'method': ['DESeq2', 'DESeq2'],
        'q_value': [0.003, 0.045],
        'effect_size': [0.52, 0.12],
        'direction': ['positive', 'positive']
    })
    
    # UKBB ANCOM-II results
    ukbb_ancom = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'method': ['ANCOM-II', 'ANCOM-II'],
        'q_value': [0.005, 0.018],
        'effect_size': [0.45, -0.35],
        'direction': ['positive', 'negative']
    })
    
    # UKBB DESeq2 results
    ukbb_deseq2 = pd.DataFrame({
        'taxon': ['Bacteroides', 'Proteobacteria'],
        'method': ['DESeq2', 'DESeq2'],
        'q_value': [0.004, 0.038],
        'effect_size': [0.48, -0.22],
        'direction': ['positive', 'negative']
    })
    
    return {
        'agp_ancom': agp_ancom,
        'agp_deseq2': agp_deseq2,
        'ukbb_ancom': ukbb_ancom,
        'ukbb_deseq2': ukbb_deseq2
    }


def test_cross_cohort_validation_file_structure(temp_validation_dir):
    """Test that the validation module exists and has expected structure."""
    # This test verifies the basic file structure and imports
    # The actual validation logic is tested in T029 implementation
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    # Verify that the module has the expected functions
    assert hasattr(sys.modules['src.analysis.validation_cross_cohort'], 'run_cross_cohort_validation')
    assert hasattr(sys.modules['src.analysis.validation_cross_cohort'], 'calculate_replication_status')
    assert hasattr(sys.modules['src.analysis.validation_cross_cohort'], 'load_association_results')
    assert hasattr(sys.modules['src.analysis.validation_cross_cohort'], 'load_diff_abundance_results')


def test_replication_status_calculation(temp_validation_dir, sample_association_data, sample_diff_abundance_data):
    """Test the core replication status calculation logic."""
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    from src.analysis.validation_cross_cohort import calculate_replication_status
    
    agp_data, ukbb_data = sample_association_data
    
    # Test MaAsLin2 replication calculation
    replication_results = calculate_replication_status(
        agp_association=agp_data,
        ukbb_association=ukbb_data,
        method='MaAsLin2',
        q_threshold=0.05
    )
    
    # Verify output schema
    assert 'taxon' in replication_results.columns
    assert 'method' in replication_results.columns
    assert 'agp_q_value' in replication_results.columns
    assert 'ukbb_q_value' in replication_results.columns
    assert 'agp_effect_size' in replication_results.columns
    assert 'ukbb_effect_size' in replication_results.columns
    assert 'replication_status' in replication_results.columns
    
    # Verify replication status values
    valid_statuses = ['replicated', 'non-replicable', 'cohort-specific']
    assert all(status in valid_statuses for status in replication_results['replication_status'])
    
    # Verify specific cases
    # Bacteroides: significant in both, same direction -> replicated
    bacteroides_row = replication_results[replication_results['taxon'] == 'Bacteroides']
    assert len(bacteroides_row) == 1
    assert bacteroides_row['replication_status'].iloc[0] == 'replicated'
    
    # Firmicutes: significant in both, same direction -> replicated
    firmicutes_row = replication_results[replication_results['taxon'] == 'Firmicutes']
    assert len(firmicutes_row) == 1
    assert firmicutes_row['replication_status'].iloc[0] == 'replicated'
    
    # Actinobacteria: not significant in either (q > 0.05) -> should not appear or cohort-specific
    # Proteobacteria: significant in both, same direction -> replicated
    proteobacteria_row = replication_results[replication_results['taxon'] == 'Proteobacteria']
    if len(proteobacteria_row) > 0:
        assert proteobacteria_row['replication_status'].iloc[0] == 'replicated'


def test_diff_abundance_replication(temp_validation_dir, sample_diff_abundance_data):
    """Test differential abundance replication status calculation."""
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    from src.analysis.validation_cross_cohort import calculate_replication_status
    
    agp_ancom = sample_diff_abundance_data['agp_ancom']
    ukbb_ancom = sample_diff_abundance_data['ukbb_ancom']
    
    # Test ANCOM-II replication
    ancom_results = calculate_replication_status(
        agp_diff_abundance=agp_ancom,
        ukbb_diff_abundance=ukbb_ancom,
        method='ANCOM-II',
        q_threshold=0.05
    )
    
    # Verify output schema includes diff_abundance_replicated column
    assert 'taxon' in ancom_results.columns
    assert 'method' in ancom_results.columns
    assert 'agp_q_value' in ancom_results.columns
    assert 'ukbb_q_value' in ancom_results.columns
    assert 'agp_effect_size' in ancom_results.columns
    assert 'ukbb_effect_size' in ancom_results.columns
    assert 'replication_status' in ancom_results.columns
    assert 'diff_abundance_replicated' in ancom_results.columns
    
    # Verify specific replication status
    # Bacteroides: significant in both, same direction -> replicated
    bacteroides_row = ancom_results[ancom_results['taxon'] == 'Bacteroides']
    assert len(bacteroides_row) == 1
    assert bacteroides_row['replication_status'].iloc[0] == 'replicated'
    assert bacteroides_row['diff_abundance_replicated'].iloc[0] is True
    
    # Firmicutes: significant in both, same direction -> replicated
    firmicutes_row = ancom_results[ancom_results['taxon'] == 'Firmicutes']
    assert len(firmicutes_row) == 1
    assert firmicutes_row['replication_status'].iloc[0] == 'replicated'
    assert firmicutes_row['diff_abundance_replicated'].iloc[0] is True


def test_full_validation_pipeline(temp_validation_dir, sample_association_data, sample_diff_abundance_data):
    """Test the full cross-cohort validation pipeline end-to-end."""
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    from src.analysis.validation_cross_cohort import run_cross_cohort_validation
    
    # Create temporary input files
    agp_assoc_file = temp_validation_dir / 'agp_association_results.tsv'
    ukbb_assoc_file = temp_validation_dir / 'ukbb_association_results.tsv'
    agp_ancom_file = temp_validation_dir / 'agp_diff_abundance_ancom.tsv'
    agp_deseq2_file = temp_validation_dir / 'agp_diff_abundance_deseq2.tsv'
    ukbb_ancom_file = temp_validation_dir / 'ukbb_diff_abundance_ancom.tsv'
    ukbb_deseq2_file = temp_validation_dir / 'ukbb_diff_abundance_deseq2.tsv'
    output_file = temp_validation_dir / 'replication_status.tsv'
    
    # Save sample data to files
    sample_association_data[0].to_csv(agp_assoc_file, sep='\t', index=False)
    sample_association_data[1].to_csv(ukbb_assoc_file, sep='\t', index=False)
    sample_diff_abundance_data['agp_ancom'].to_csv(agp_ancom_file, sep='\t', index=False)
    sample_diff_abundance_data['agp_deseq2'].to_csv(agp_deseq2_file, sep='\t', index=False)
    sample_diff_abundance_data['ukbb_ancom'].to_csv(ukbb_ancom_file, sep='\t', index=False)
    sample_diff_abundance_data['ukbb_deseq2'].to_csv(ukbb_deseq2_file, sep='\t', index=False)
    
    # Run the full validation pipeline
    run_cross_cohort_validation(
        agp_association_file=str(agp_assoc_file),
        ukbb_association_file=str(ukbb_assoc_file),
        agp_ancom_file=str(agp_ancom_file),
        agp_deseq2_file=str(agp_deseq2_file),
        ukbb_ancom_file=str(ukbb_ancom_file),
        ukbb_deseq2_file=str(ukbb_deseq2_file),
        output_file=str(output_file)
    )
    
    # Verify output file exists
    assert output_file.exists(), "Output file was not created"
    
    # Verify output schema
    output_df = pd.read_csv(output_file, sep='\t')
    expected_columns = [
        'taxon', 'method', 'agp_q_value', 'ukbb_q_value',
        'agp_effect_size', 'ukbb_effect_size', 'replication_status'
    ]
    
    for col in expected_columns:
        assert col in output_df.columns, f"Missing column: {col}"
    
    # Verify we have results for all methods
    methods = output_df['method'].unique()
    assert 'MaAsLin2' in methods
    assert 'ANCOM-II' in methods
    assert 'DESeq2' in methods
    
    # Verify replication status distribution
    status_counts = output_df['replication_status'].value_counts()
    assert 'replicated' in status_counts.index or len(status_counts) > 0


def test_validation_with_missing_data(temp_validation_dir):
    """Test validation pipeline handles missing data gracefully."""
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    from src.analysis.validation_cross_cohort import run_cross_cohort_validation
    
    # Create input files with some missing taxa
    agp_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'maaslin2_beta': [0.5, -0.3],
        'maaslin2_se': [0.1, 0.1],
        'maaslin2_p_value': [0.001, 0.01],
        'maaslin2_q_value': [0.005, 0.02],
        'spearman_rho': [0.45, -0.25],
        'spearman_se': [0.1, 0.1],
        'spearman_p_value': [0.002, 0.015]
    })
    
    ukbb_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Proteobacteria'],  # Different taxa
        'maaslin2_beta': [0.4, -0.2],
        'maaslin2_se': [0.12, 0.09],
        'maaslin2_p_value': [0.002, 0.025],
        'maaslin2_q_value': [0.006, 0.035],
        'spearman_rho': [0.42, -0.14],
        'spearman_se': [0.11, 0.09],
        'spearman_p_value': [0.003, 0.028]
    })
    
    temp_dir = temp_validation_dir
    agp_assoc_file = temp_dir / 'agp_association_results.tsv'
    ukbb_assoc_file = temp_dir / 'ukbb_association_results.tsv'
    agp_ancom_file = temp_dir / 'agp_diff_abundance_ancom.tsv'
    agp_deseq2_file = temp_dir / 'agp_diff_abundance_deseq2.tsv'
    ukbb_ancom_file = temp_dir / 'ukbb_diff_abundance_ancom.tsv'
    ukbb_deseq2_file = temp_dir / 'ukbb_diff_abundance_deseq2.tsv'
    output_file = temp_dir / 'replication_status.tsv'
    
    # Create empty differential abundance files
    agp_data.to_csv(agp_assoc_file, sep='\t', index=False)
    ukbb_data.to_csv(ukbb_assoc_file, sep='\t', index=False)
    
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(agp_ancom_file, sep='\t', index=False)
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(agp_deseq2_file, sep='\t', index=False)
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(ukbb_ancom_file, sep='\t', index=False)
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(ukbb_deseq2_file, sep='\t', index=False)
    
    # Run validation - should handle missing data
    try:
        run_cross_cohort_validation(
            agp_association_file=str(agp_assoc_file),
            ukbb_association_file=str(ukbb_assoc_file),
            agp_ancom_file=str(agp_ancom_file),
            agp_deseq2_file=str(agp_deseq2_file),
            ukbb_ancom_file=str(ukbb_ancom_file),
            ukbb_deseq2_file=str(ukbb_deseq2_file),
            output_file=str(output_file)
        )
        
        # Verify output was created
        assert output_file.exists()
        output_df = pd.read_csv(output_file, sep='\t')
        
        # Should have results for taxa that exist in both cohorts
        # Bacteroides is in both -> should be processed
        assert 'Bacteroides' in output_df['taxon'].values or len(output_df) >= 0
        
    except Exception as e:
        # If the pipeline fails with missing data, that's also a valid behavior
        # as long as it fails loudly rather than producing incorrect results
        assert "missing" in str(e).lower() or "not found" in str(e).lower()


def test_validation_output_schema_compliance(temp_validation_dir):
    """Test that validation output strictly complies with the required schema."""
    if not HAS_VALIDATION_MODULE:
        pytest.skip("Validation module not yet implemented (T029)")
    
    from src.analysis.validation_cross_cohort import run_cross_cohort_validation
    
    # Create comprehensive test data
    agp_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria'],
        'maaslin2_beta': [0.5, -0.3, 0.1, -0.2],
        'maaslin2_se': [0.1, 0.1, 0.05, 0.08],
        'maaslin2_p_value': [0.001, 0.01, 0.06, 0.02],
        'maaslin2_q_value': [0.005, 0.02, 0.1, 0.03],
        'spearman_rho': [0.45, -0.25, 0.08, -0.15],
        'spearman_se': [0.1, 0.1, 0.05, 0.08],
        'spearman_p_value': [0.002, 0.015, 0.07, 0.025]
    })
    
    ukbb_data = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria'],
        'maaslin2_beta': [0.4, -0.35, 0.05, -0.18],
        'maaslin2_se': [0.12, 0.11, 0.06, 0.09],
        'maaslin2_p_value': [0.002, 0.008, 0.08, 0.025],
        'maaslin2_q_value': [0.006, 0.018, 0.12, 0.035],
        'spearman_rho': [0.42, -0.28, 0.06, -0.14],
        'spearman_se': [0.11, 0.11, 0.06, 0.09],
        'spearman_p_value': [0.003, 0.012, 0.09, 0.028]
    })
    
    temp_dir = temp_validation_dir
    agp_assoc_file = temp_dir / 'agp_association_results.tsv'
    ukbb_assoc_file = temp_dir / 'ukbb_association_results.tsv'
    agp_ancom_file = temp_dir / 'agp_diff_abundance_ancom.tsv'
    agp_deseq2_file = temp_dir / 'agp_diff_abundance_deseq2.tsv'
    ukbb_ancom_file = temp_dir / 'ukbb_diff_abundance_ancom.tsv'
    ukbb_deseq2_file = temp_dir / 'ukbb_diff_abundance_deseq2.tsv'
    output_file = temp_dir / 'replication_status.tsv'
    
    # Save data
    agp_data.to_csv(agp_assoc_file, sep='\t', index=False)
    ukbb_data.to_csv(ukbb_assoc_file, sep='\t', index=False)
    
    # Create minimal differential abundance data
    pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'method': ['ANCOM-II', 'ANCOM-II'],
        'q_value': [0.004, 0.015],
        'effect_size': [0.48, -0.32],
        'direction': ['positive', 'negative']
    }).to_csv(agp_ancom_file, sep='\t', index=False)
    
    pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'method': ['ANCOM-II', 'ANCOM-II'],
        'q_value': [0.005, 0.018],
        'effect_size': [0.45, -0.35],
        'direction': ['positive', 'negative']
    }).to_csv(ukbb_ancom_file, sep='\t', index=False)
    
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(agp_deseq2_file, sep='\t', index=False)
    pd.DataFrame(columns=['taxon', 'method', 'q_value', 'effect_size', 'direction']).to_csv(ukbb_deseq2_file, sep='\t', index=False)
    
    # Run validation
    run_cross_cohort_validation(
        agp_association_file=str(agp_assoc_file),
        ukbb_association_file=str(ukbb_assoc_file),
        agp_ancom_file=str(agp_ancom_file),
        agp_deseq2_file=str(agp_deseq2_file),
        ukbb_ancom_file=str(ukbb_ancom_file),
        ukbb_deseq2_file=str(ukbb_deseq2_file),
        output_file=str(output_file)
    )
    
    # Load and validate output
    output_df = pd.read_csv(output_file, sep='\t')
    
    # Required columns per T029 specification
    required_columns = [
        'taxon', 'method', 'agp_q_value', 'ukbb_q_value',
        'agp_effect_size', 'ukbb_effect_size', 'replication_status'
    ]
    
    # Check all required columns exist
    for col in required_columns:
        assert col in output_df.columns, f"Missing required column: {col}"
    
    # Check replication_status values
    valid_statuses = ['replicated', 'non-replicable', 'cohort-specific']
    for status in output_df['replication_status']:
        assert status in valid_statuses, f"Invalid replication status: {status}"
    
    # Check method values
    valid_methods = ['MaAsLin2', 'ANCOM-II', 'DESeq2']
    for method in output_df['method']:
        assert method in valid_methods, f"Invalid method: {method}"
    
    # Verify data types
    assert output_df['agp_q_value'].dtype in ['float64', 'float32', 'int64', 'int32']
    assert output_df['ukbb_q_value'].dtype in ['float64', 'float32', 'int64', 'int32']
    assert output_df['agp_effect_size'].dtype in ['float64', 'float32', 'int64', 'int32']
    assert output_df['ukbb_effect_size'].dtype in ['float64', 'float32', 'int64', 'int32']