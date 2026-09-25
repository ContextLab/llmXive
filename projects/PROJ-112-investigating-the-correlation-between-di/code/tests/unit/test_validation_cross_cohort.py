import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from src.analysis.validation_cross_cohort import (
    determine_replication_status,
    load_association_data,
    load_diff_abundance_data,
    merge_replication_results,
    run_validation_cross_cohort
)

def test_determine_replication_status_replicated():
    # Both significant, same direction
    status = determine_replication_status(0.5, 0.6, 0.01, 0.01)
    assert status == 'replicated'

    status = determine_replication_status(-0.5, -0.6, 0.01, 0.01)
    assert status == 'replicated'

def test_determine_replication_status_non_replicable_opposite():
    # Both significant, opposite direction
    status = determine_replication_status(0.5, -0.6, 0.01, 0.01)
    assert status == 'non-replicable'

    status = determine_replication_status(-0.5, 0.6, 0.01, 0.01)
    assert status == 'non-replicable'

def test_determine_replication_status_cohort_specific():
    # One significant, one not
    status = determine_replication_status(0.5, 0.6, 0.01, 0.1)
    assert status == 'cohort-specific'

    status = determine_replication_status(0.5, 0.6, 0.1, 0.01)
    assert status == 'cohort-specific'

def test_determine_replication_status_non_replicable_neither():
    # Neither significant
    status = determine_replication_status(0.5, 0.6, 0.1, 0.1)
    assert status == 'non-replicable'

def test_load_association_data(tmp_path):
    # Create a mock association file
    data = {
        'taxon': ['taxon1', 'taxon2'],
        'maaslin2_beta': [0.5, -0.3],
        'maaslin2_se': [0.1, 0.1],
        'maaslin2_p_value': [0.01, 0.05],
        'maaslin2_q_value': [0.01, 0.05],
        'spearman_rho': [0.4, -0.2],
        'spearman_se': [0.1, 0.1],
        'spearman_p_value': [0.02, 0.06],
        'cohort': ['AGP', 'UKBB']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "association_results.tsv"
    df.to_csv(file_path, sep='\t', index=False)

    loaded = load_association_data(file_path)
    assert len(loaded) == 2
    assert 'taxon' in loaded.columns
    assert 'maaslin2_beta' in loaded.columns
    assert 'maaslin2_q_value' in loaded.columns

def test_load_diff_abundance_data(tmp_path):
    # Create a mock diff abundance file
    data = {
        'taxon': ['taxon1', 'taxon2'],
        'method': ['ANCOM-II', 'ANCOM-II'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "diff_abundance.tsv"
    df.to_csv(file_path, sep='\t', index=False)

    loaded = load_diff_abundance_data(file_path)
    assert len(loaded) == 2
    assert 'taxon' in loaded.columns
    assert 'q-value' in loaded.columns
    assert 'effect_size' in loaded.columns

def test_merge_replication_results(tmp_path):
    # Create mock data
    maaslin2_data = {
        'taxon': ['taxon1', 'taxon2'],
        'maaslin2_beta': [0.5, -0.3],
        'maaslin2_q_value': [0.01, 0.05],
        'cohort': ['AGP', 'UKBB']
    }
    maaslin2_df = pd.DataFrame(maaslin2_data)
    maaslin2_file = tmp_path / "assoc.tsv"
    maaslin2_df.to_csv(maaslin2_file, sep='\t', index=False)

    ancom_agp_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    ancom_agp_df = pd.DataFrame(ancom_agp_data)
    ancom_agp_file = tmp_path / "ancom_agp.tsv"
    ancom_agp_df.to_csv(ancom_agp_file, sep='\t', index=False)

    ancom_ukbb_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    ancom_ukbb_df = pd.DataFrame(ancom_ukbb_data)
    ancom_ukbb_file = tmp_path / "ancom_ukbb.tsv"
    ancom_ukbb_df.to_csv(ancom_ukbb_file, sep='\t', index=False)

    deseq2_agp_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    deseq2_agp_df = pd.DataFrame(deseq2_agp_data)
    deseq2_agp_file = tmp_path / "deseq2_agp.tsv"
    deseq2_agp_df.to_csv(deseq2_agp_file, sep='\t', index=False)

    deseq2_ukbb_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    deseq2_ukbb_df = pd.DataFrame(deseq2_ukbb_data)
    deseq2_ukbb_file = tmp_path / "deseq2_ukbb.tsv"
    deseq2_ukbb_df.to_csv(deseq2_ukbb_file, sep='\t', index=False)

    # We need to split maaslin2 by cohort for the merge function
    # But our function expects a single dataframe with cohort column
    # So we'll pass the merged maaslin2_df and let the function split it
    result = merge_replication_results(
        maaslin2_df,
        ancom_agp_df,
        ancom_ukbb_df,
        deseq2_agp_df,
        deseq2_ukbb_df,
        q_threshold=0.05
    )

    assert len(result) == 6  # 2 taxa * 3 methods
    assert 'replication_status' in result.columns
    assert 'MaAsLin2' in result['method'].values
    assert 'ANCOM-II' in result['method'].values
    assert 'DESeq2' in result['method'].values

def test_run_validation_cross_cohort(tmp_path):
    # Create mock input files
    maaslin2_data = {
        'taxon': ['taxon1', 'taxon2'],
        'maaslin2_beta': [0.5, -0.3],
        'maaslin2_q_value': [0.01, 0.05],
        'cohort': ['AGP', 'UKBB']
    }
    maaslin2_df = pd.DataFrame(maaslin2_data)
    maaslin2_file = tmp_path / "assoc.tsv"
    maaslin2_df.to_csv(maaslin2_file, sep='\t', index=False)

    ancom_agp_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    ancom_agp_df = pd.DataFrame(ancom_agp_data)
    ancom_agp_file = tmp_path / "ancom_agp.tsv"
    ancom_agp_df.to_csv(ancom_agp_file, sep='\t', index=False)

    ancom_ukbb_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    ancom_ukbb_df = pd.DataFrame(ancom_ukbb_data)
    ancom_ukbb_file = tmp_path / "ancom_ukbb.tsv"
    ancom_ukbb_df.to_csv(ancom_ukbb_file, sep='\t', index=False)

    deseq2_agp_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    deseq2_agp_df = pd.DataFrame(deseq2_agp_data)
    deseq2_agp_file = tmp_path / "deseq2_agp.tsv"
    deseq2_agp_df.to_csv(deseq2_agp_file, sep='\t', index=False)

    deseq2_ukbb_data = {
        'taxon': ['taxon1', 'taxon2'],
        'q-value': [0.01, 0.05],
        'effect_size': [0.5, -0.3],
        'direction': ['positive', 'negative']
    }
    deseq2_ukbb_df = pd.DataFrame(deseq2_ukbb_data)
    deseq2_ukbb_file = tmp_path / "deseq2_ukbb.tsv"
    deseq2_ukbb_df.to_csv(deseq2_ukbb_file, sep='\t', index=False)

    output_file = tmp_path / "replication_status.tsv"

    run_validation_cross_cohort(
        association_file=maaslin2_file,
        ancom_agp_file=ancom_agp_file,
        ancom_ukbb_file=ancom_ukbb_file,
        deseq2_agp_file=deseq2_agp_file,
        deseq2_ukbb_file=deseq2_ukbb_file,
        output_file=output_file,
        q_threshold=0.05
    )

    assert output_file.exists()
    result_df = pd.read_csv(output_file, sep='\t')
    assert len(result_df) == 6
    assert 'replication_status' in result_df.columns
    assert 'taxon' in result_df.columns
    assert 'method' in result_df.columns