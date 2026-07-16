"""Integration tests verifying data flow between modules."""
import pytest
import numpy as np
from data_models import PolymerRecord, MolecularGraph
from utils import get_logger

logger = get_logger(__name__)

def test_record_to_graph_conversion_flow():
    """
    Integration test: Verify that a PolymerRecord can be conceptually 
    linked to a MolecularGraph structure (mocking the conversion logic).
    """
    # 1. Create a record
    record = PolymerRecord(
        id="int_001",
        smiles="CC(=O)OC", # Methyl acetate (simple ester)
        degradation_pathway="hydrolysis",
        temperature=300.0,
        ph=5.0,
        uv_intensity=0.0
    )
    
    # 2. Simulate graph creation (since we don't have the full RDKit pipeline in utils yet)
    # In a real integration test, we would import the actual converter from preprocess.py
    # Here we verify the data structures are compatible
    node_features = np.random.rand(10, 5) # 10 nodes, 5 features
    edge_index = np.random.randint(0, 10, (2, 20))
    edge_features = np.random.rand(20, 3)
    
    graph = MolecularGraph(
        node_features=node_features,
        edge_index=edge_index,
        edge_features=edge_features,
        smiles=record.smiles
    )
    
    # 3. Verify consistency
    assert graph.smiles == record.smiles
    assert len(graph.node_features) == 10
    
    logger.info(f"Successfully created graph for record {record.id} with {len(graph.node_features)} nodes")
    
def test_config_and_logging_integration():
    """Test that logging and config utilities work together in a test flow."""
    from utils import load_config, setup_logging
    
    # Setup logging
    setup_logging(level="DEBUG")
    
    # Load config (simulated)
    config = load_config()
    
    # Verify we can log using the config
    logger.debug(f"Config loaded: {list(config.keys())}")
    
    assert isinstance(config, dict)