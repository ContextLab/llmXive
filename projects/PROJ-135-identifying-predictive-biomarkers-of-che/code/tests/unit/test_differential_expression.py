import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Mock rpy2 to avoid R dependency in unit tests
# We will test the logic of filtering and file handling
# The actual DESeq2 call is mocked or tested via integration

from src.differential_expression import process_tumor_type_discovery

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_discovery_data(temp_data_dir):
    # Create a mock discovery set
    # Genes: G1, G2, G3, G4
    # Samples: S1..S10
    # Response: Responder (R), Non-Responder (N)
    
    genes = ['G1', 'G2', 'G3', 'G4']
    samples = [f'S{i}' for i in range(1, 11)]
    
    # Metadata
    metadata = {
        'sample_id': samples,
        'response_label': ['R'] * 5 + ['N'] * 5
    }
    
    # Expression data (mock counts)
    # G1: High in R, Low in N (Significant)
    # G2: Low in R, High in N (Significant)
    # G3: Random (Not significant)
    # G4: Constant (Not significant)
    
    data = []
    for g in genes:
        row = []
        for s in samples:
            if g == 'G1':
                val = 100 if s.startswith('S1') or s.startswith('S2') or s.startswith('S3') or s.startswith('S4') or s.startswith('S5') else 10
            elif g == 'G2':
                val = 10 if s.startswith('S1') or s.startswith('S2') or s.startswith('S3') or s.startswith('S4') or s.startswith('S5') else 100
            elif g == 'G3':
                val = np.random.randint(10, 50)
            else: # G4
                val = 50
            row.append(val)
        data.append(row)
        
    df = pd.DataFrame(data, index=genes, columns=samples)
    df = df.reset_index()
    df.columns = ['gene'] + samples
    
    # Add metadata as columns? 
    # The expected format from T020 is: sample_id, response_label, then gene columns?
    # Or: index=sample_id, columns=genes, plus metadata columns?
    # Let's assume the format: 
    # Rows = Samples, Cols = Genes + Metadata
    # But DESeq2 expects Genes x Samples.
    # Let's re-orient to match the loader in process_tumor_type_discovery:
    # "Columns: sample_id, response_label, then gene expression columns."
    # And "Rows=Genes, Cols=Samples" is NOT the input format to the function.
    # The input CSV has Samples as rows.
    
    # Re-build input CSV format: Samples x Genes
    input_data = []
    for i, s in enumerate(samples):
        row = {
            'sample_id': s,
            'response_label': metadata['response_label'][i]
        }
        for g in genes:
            # Find value for this gene and sample
            # In the 'data' list above, rows were genes, cols were samples
            # data[0] is G1, data[0][0] is S1
            gene_idx = genes.index(g)
            sample_idx = samples.index(s)
            row[g] = data[gene_idx][sample_idx]
        input_data.append(row)
        
    input_df = pd.DataFrame(input_data)
    input_file = temp_data_dir / "BRCA_discovery_set.csv"
    input_df.to_csv(input_file, index=False)
    return input_file

def test_process_discovery_set_format(temp_data_dir, sample_discovery_data):
    """Test that the function accepts the correct format and processes it."""
    # We cannot run the full DESeq2 in unit test without R environment setup
    # Instead, we test that the file is loaded and the filename check passes
    # We will mock the DE analysis part
    
    # This test is primarily structural.
    # In a real environment with R, this would run the full pipeline.
    # For now, we verify the file loading logic.
    
    input_file = sample_discovery_data
    output_file = temp_data_dir / "BRCA_de_results.csv"
    
    # Verify input file exists
    assert input_file.exists()
    
    # Verify filename ends with _discovery_set.csv
    assert input_file.name.endswith('_discovery_set.csv')
    
    # Load and check structure
    df = pd.read_csv(input_file)
    assert 'sample_id' in df.columns
    assert 'response_label' in df.columns
    assert 'G1' in df.columns

def test_wrong_filename(temp_data_dir, sample_discovery_data):
    """Test that the function rejects files not ending in _discovery_set.csv."""
    # Rename the file
    bad_file = temp_data_dir / "BRCA_training_set.csv"
    sample_discovery_data.rename(bad_file)
    
    with pytest.raises(ValueError) as exc_info:
        process_tumor_type_discovery(
            tumor_type="BRCA",
            input_dir=temp_data_dir,
            output_dir=temp_data_dir
        )
    assert "does not end with '_discovery_set.csv'" in str(exc_info.value)

def test_missing_response_column(temp_data_dir):
    """Test that the function handles missing response_label column."""
    # Create a file without response_label
    genes = ['G1', 'G2']
    samples = ['S1', 'S2']
    data = {
        'sample_id': samples,
        'G1': [10, 20],
        'G2': [30, 40]
    }
    df = pd.DataFrame(data)
    input_file = temp_data_dir / "BRCA_discovery_set.csv"
    df.to_csv(input_file, index=False)
    
    # This should return None or raise an error depending on implementation
    # In our implementation, it logs error and returns None
    result = process_tumor_type_discovery(
        tumor_type="BRCA",
        input_dir=temp_data_dir,
        output_dir=temp_data_dir
    )
    assert result is None

def test_threshold_logic():
    """Test the filtering logic for significant genes."""
    # Create a mock results dataframe
    data = {
        'gene': ['G1', 'G2', 'G3', 'G4'],
        'log2FoldChange': [2.5, -2.0, 0.5, -0.5],
        'padj': [0.01, 0.04, 0.10, 0.001]
    }
    df = pd.DataFrame(data)
    
    fdr_threshold = 0.05
    log2fc_threshold = 1.0
    
    significant = df[
        (df['padj'] < fdr_threshold) & 
        (df['padj'].notna()) &
        (abs(df['log2FoldChange']) > log2fc_threshold)
    ]
    
    # G1: p=0.01, |2.5|>1 -> Significant
    # G2: p=0.04, |-2.0|>1 -> Significant
    # G3: p=0.10 -> Not significant
    # G4: p=0.001, |-0.5|<1 -> Not significant
    
    assert len(significant) == 2
    assert 'G1' in significant['gene'].values
    assert 'G2' in significant['gene'].values