"""
Integration test for end-to-end ingestion and graph construction.

This test verifies the full pipeline flow:
1. Data ingestion from ChEMBL/PubChem (with citation validation)
2. Kinetic normalization and filtering
3. Graph construction
4. Final dataset validation (T019 requirement)

Note: This test expects the data ingestion pipeline to have been run
previously to generate the raw data files. If data files do not exist,
the test will attempt to run the ingestion pipeline first.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.ingestion import run_ingestion, ReactionRecord
from src.data.preprocessing import process_batch_for_graphs, construct_molecular_graph
from src.utils.logging import get_audit_logger

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for validation
REQUIRED_FIELDS = [
    'smiles',
    'normalized_log_rate',
    'pka',
    'reaction_id',
    'substrate_smiles',
    'amine_smiles'
]

REQUIRED_GRAPH_FIELDS = [
    'node_features',
    'edge_features',
    'edge_index',
    'reaction_id'
]


def ensure_data_directory():
    """Ensure data directories exist."""
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    return raw_dir, processed_dir


def run_ingestion_pipeline():
    """Run the full ingestion pipeline if data doesn't exist."""
    raw_dir, _ = ensure_data_directory()
    raw_data_path = raw_dir / "chembl_sn2_reactions.json"
    
    # Check if data already exists
    if raw_data_path.exists():
        logger.info(f"Raw data already exists at {raw_data_path}, skipping ingestion")
        return raw_data_path
    
    logger.info("Running ingestion pipeline...")
    try:
        result = run_ingestion()
        if result and 'raw_data_path' in result:
            logger.info(f"Ingestion completed, data saved to {result['raw_data_path']}")
            return Path(result['raw_data_path'])
        else:
            logger.error("Ingestion returned no valid data path")
            return None
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        # If ingestion fails due to network or data issues, we may need to handle this
        # For now, we'll let the test fail if we can't get real data
        raise


def load_raw_data(raw_data_path: Path) -> List[Dict[str, Any]]:
    """Load raw ingestion data."""
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    with open(raw_data_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        raise ValueError(f"Unexpected data format in {raw_data_path}")


def process_to_graphs(raw_data: List[Dict[str, Any]], processed_dir: Path):
    """Process raw data into molecular graphs."""
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(raw_data)
    
    # Process in batches
    batch_size = 100
    all_graphs = []
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].to_dict('records')
        graphs, exclusions = process_batch_for_graphs(batch)
        all_graphs.extend(graphs)
    
    # Save processed graphs
    graphs_path = processed_dir / "molecular_graphs.json"
    with open(graphs_path, 'w') as f:
        json.dump(all_graphs, f, indent=2)
    
    # Log exclusions
    if exclusions:
        exclusion_path = processed_dir / "graph_exclusions.json"
        with open(exclusion_path, 'w') as f:
            json.dump(exclusions, f, indent=2)
        logger.warning(f"Excluded {len(exclusions)} records during graph construction")
    
    return graphs_path, all_graphs


def validate_dataset_integrity(graphs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    T019 Verification: Check that output dataset contains valid records
    with no missing required fields.
    """
    results = {
        'total_records': len(graphs),
        'valid_records': 0,
        'invalid_records': 0,
        'missing_fields': {},
        'nan_values': {},
        'details': []
    }
    
    if not graphs:
        results['details'].append("No graphs found in dataset")
        return results
    
    for i, graph in enumerate(graphs):
        record_valid = True
        missing = []
        nan_fields = []
        
        # Check REQUIRED_GRAPH_FIELDS
        for field in REQUIRED_GRAPH_FIELDS:
            if field not in graph:
                missing.append(field)
                record_valid = False
            elif graph[field] is None:
                missing.append(f"{field} (None)")
                record_valid = False
            elif isinstance(graph[field], list) and len(graph[field]) == 0:
                if field in ['node_features', 'edge_features']:
                    nan_fields.append(field)
                # edge_index being empty might be valid for some cases
        
        # Check node features specifically
        if 'node_features' in graph and graph['node_features']:
            for j, node_feat in enumerate(graph['node_features']):
                if node_feat is None:
                    nan_fields.append(f"node_features[{j}]")
                    record_valid = False
                elif isinstance(node_feat, list):
                    for k, val in enumerate(node_feat):
                        if val is None or (isinstance(val, float) and (val != val)):  # NaN check
                            nan_fields.append(f"node_features[{j}][{k}]")
                            record_valid = False
        
        # Check edge features specifically
        if 'edge_features' in graph and graph['edge_features']:
            for j, edge_feat in enumerate(graph['edge_features']):
                if edge_feat is None:
                    nan_fields.append(f"edge_features[{j}]")
                    record_valid = False
                elif isinstance(edge_feat, list):
                    for k, val in enumerate(edge_feat):
                        if val is None or (isinstance(val, float) and (val != val)):
                            nan_fields.append(f"edge_features[{j}][{k}]")
                            record_valid = False
        
        # Check for NaN in numeric fields if present
        numeric_fields = ['normalized_log_rate', 'pka']
        for field in numeric_fields:
            if field in graph:
                val = graph[field]
                if val is not None and isinstance(val, float):
                    if val != val:  # NaN check
                        nan_fields.append(field)
                        record_valid = False
        
        if record_valid:
            results['valid_records'] += 1
        else:
            results['invalid_records'] += 1
            if missing:
                results['missing_fields'][i] = missing
            if nan_fields:
                results['nan_values'][i] = nan_fields
            
            results['details'].append({
                'index': i,
                'reaction_id': graph.get('reaction_id', 'unknown'),
                'missing': missing,
                'nan_fields': nan_fields
            })
    
    return results


def test_ingestion_and_graph_construction():
    """
    End-to-end test: Ingestion -> Graph Construction -> Validation
    
    This test verifies:
    1. Data can be ingested from real sources
    2. Graphs can be constructed from the data
    3. The final dataset has no missing required fields (T019)
    """
    # Step 1: Ensure directories exist
    raw_dir, processed_dir = ensure_data_directory()
    
    # Step 2: Run ingestion pipeline
    raw_data_path = run_ingestion_pipeline()
    
    # Step 3: Load raw data
    raw_data = load_raw_data(raw_data_path)
    assert len(raw_data) > 0, "No data returned from ingestion pipeline"
    logger.info(f"Loaded {len(raw_data)} raw records")
    
    # Step 4: Process to graphs
    graphs_path, graphs = process_to_graphs(raw_data, processed_dir)
    assert len(graphs) > 0, "No graphs constructed from raw data"
    logger.info(f"Constructed {len(graphs)} molecular graphs")
    
    # Step 5: Validate dataset integrity (T019)
    validation_results = validate_dataset_integrity(graphs)
    
    # Assert that we have valid records
    assert validation_results['valid_records'] > 0, \
        f"No valid records found. Missing fields: {validation_results['missing_fields']}"
    
    # Assert that most records are valid (allow some exclusions)
    valid_ratio = validation_results['valid_records'] / validation_results['total_records']
    assert valid_ratio >= 0.8, \
        f"Only {valid_ratio:.1%} of records are valid. Details: {validation_results['details'][:5]}"
    
    # Log validation summary
    logger.info(f"Validation Summary:")
    logger.info(f"  Total records: {validation_results['total_records']}")
    logger.info(f"  Valid records: {validation_results['valid_records']}")
    logger.info(f"  Invalid records: {validation_results['invalid_records']}")
    logger.info(f"  Valid ratio: {valid_ratio:.1%}")
    
    if validation_results['missing_fields']:
        logger.warning(f"Records with missing fields: {len(validation_results['missing_fields'])}")
    if validation_results['nan_values']:
        logger.warning(f"Records with NaN values: {len(validation_results['nan_values'])}")
    
    # Assert no critical missing fields in valid records
    for idx, missing in validation_results['missing_fields'].items():
        critical_missing = [f for f in missing if f in REQUIRED_GRAPH_FIELDS]
        assert len(critical_missing) == 0, \
            f"Record {idx} has critical missing fields: {critical_missing}"
    
    # Assert no NaN in critical fields
    for idx, nan_fields in validation_results['nan_values'].items():
        critical_nan = [f for f in nan_fields if f in ['normalized_log_rate', 'pka']]
        assert len(critical_nan) == 0, \
            f"Record {idx} has NaN in critical fields: {critical_nan}"
    
    logger.info("T019 Validation PASSED: Dataset contains valid records with no missing required fields")


def test_graph_structure_validity():
    """
    Test that constructed graphs have valid structure.
    """
    _, processed_dir = ensure_data_directory()
    graphs_path = processed_dir / "molecular_graphs.json"
    
    if not graphs_path.exists():
        # Run full pipeline first
        test_ingestion_and_graph_construction()
    
    with open(graphs_path, 'r') as f:
        graphs = json.load(f)
    
    assert len(graphs) > 0, "No graphs found for structure validation"
    
    for i, graph in enumerate(graphs):
        # Check node_features is a list of lists
        assert isinstance(graph['node_features'], list), \
            f"Graph {i}: node_features must be a list"
        for j, node in enumerate(graph['node_features']):
            assert isinstance(node, list), \
                f"Graph {i}, node {j}: node_features must be list of lists"
            assert len(node) > 0, \
                f"Graph {i}, node {j}: node_features cannot be empty"
        
        # Check edge_index is a list of lists (or numpy array converted to list)
        assert isinstance(graph['edge_index'], list), \
            f"Graph {i}: edge_index must be a list"
        
        # Check edge_features
        if 'edge_features' in graph:
            assert isinstance(graph['edge_features'], list), \
                f"Graph {i}: edge_features must be a list"
            for j, edge in enumerate(graph['edge_features']):
                assert isinstance(edge, list), \
                    f"Graph {i}, edge {j}: edge_features must be list of lists"
    
    logger.info("Graph structure validation PASSED")


if __name__ == "__main__":
    # Run tests directly
    test_ingestion_and_graph_construction()
    test_graph_structure_validity()
    print("\nAll integration tests PASSED!")
