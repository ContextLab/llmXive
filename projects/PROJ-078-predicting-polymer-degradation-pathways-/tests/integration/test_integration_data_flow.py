"""
Integration tests for data flow from raw records to processed graphs.
"""
import pytest
import tempfile
import os
from pathlib import Path
from data_models import PolymerRecord
from preprocess import filter_missing_environmental_data, filter_polyesters, smiles_to_molecular_graph
from ingest import validate_degradation_label

def test_filter_missing_environmental_data(sample_polymer_record_dict, sample_polymer_record_missing_env):
    """Test that records with missing environmental data are excluded."""
    records = [
        PolymerRecord(**sample_polymer_record_dict),
        PolymerRecord(**sample_polymer_record_missing_env)
    ]
    filtered = filter_missing_environmental_data(records)
    assert len(filtered) == 1
    assert filtered[0].smiles == sample_polymer_record_dict["smiles"]

def test_filter_polyesters(sample_polymer_record_dict):
    """Test that polyester filtering works on valid records."""
    # Methyl acetate is an ester
    records = [PolymerRecord(**sample_polymer_record_dict)]
    filtered = filter_polyesters(records)
    # Should keep the ester
    assert len(filtered) == 1

def test_smiles_to_graph_conversion(sample_polymer_record_dict):
    """Test conversion of a polymer record to a molecular graph."""
    record = PolymerRecord(**sample_polymer_record_dict)
    graph = smiles_to_molecular_graph(record.smiles)
    assert graph is not None
    assert graph.num_nodes > 0
    assert graph.num_edges > 0
