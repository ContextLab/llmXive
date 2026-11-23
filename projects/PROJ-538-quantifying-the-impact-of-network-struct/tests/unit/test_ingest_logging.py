import pytest
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.ingest import DataAudit, RealDataLoader, SyntheticDataGenerator, DefectGraphBuilder, run_ingestion_pipeline
from code.utils import get_logger, log_audit_event
from code.models import AtomicSnapshot

def test_data_audit_logging():
    """Test that DataAudit logs events correctly."""
    audit = DataAudit(Path("data"))
    
    # Mock the logger to capture calls
    with patch.object(audit, 'logger') as mock_logger:
        result = audit.audit_source("test_source")
        
        mock_logger.info.assert_any_call("Auditing data source: test_source")
        assert result["source"] == "test_source"

def test_real_data_loader_logging():
    """Test that RealDataLoader logs load events."""
    loader = RealDataLoader(Path("data"))
    
    with patch.object(loader, 'logger') as mock_logger:
        # This will fail in real execution due to missing data, but we test the logging path
        # We mock the internal check to avoid raising DataAvailabilityError
        with patch('code.ingest.AtomicSnapshot') as mock_snap_class:
            mock_snap = MagicMock()
            mock_snap.thermal_conductivity_W_m_K = 150.0
            mock_snap_class.return_value = mock_snap
            
            try:
                loader.load("test_source")
            except:
                pass # Ignore errors in mock, we just check logs
            
            mock_logger.info.assert_any_call("Loading real data from source: test_source")

def test_defect_graph_builder_logging():
    """Test that DefectGraphBuilder logs graph construction."""
    builder = DefectGraphBuilder()
    
    # Create a minimal valid snapshot for testing
    snap = AtomicSnapshot(
        species=["Cu", "Ni"],
        coordinates=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
        thermal_conductivity_W_m_K=100.0
    )
    
    with patch.object(builder, 'logger') as mock_logger:
        graph = builder.build(snap)
        
        mock_logger.info.assert_any_call("Building defect graph from snapshot")
        assert graph.node_count == 2

def test_run_ingestion_pipeline_logging():
    """Test that the full pipeline logs start and end events."""
    with patch('code.ingest.log_audit_event') as mock_log:
        with patch('code.ingest.logger') as mock_logger:
            # Mock the components to avoid real execution
            with patch('code.ingest.SyntheticDataGenerator') as mock_gen:
                mock_gen.return_value.generate.return_value = [
                    AtomicSnapshot(
                        species=["Cu"],
                        coordinates=[[0.0, 0.0, 0.0]],
                        thermal_conductivity_W_m_K=100.0
                    )
                ]
                
                with patch('code.ingest.DataAudit'):
                    with patch('code.ingest.DefectGraphBuilder') as mock_builder:
                        mock_builder.return_value.build.return_value = MagicMock(node_count=1, edge_count=0)
                        
                        run_ingestion_pipeline(mode="synthetic")
                        
                        mock_logger.info.assert_any_call("Starting ingestion pipeline in synthetic mode")
                        mock_logger.info.assert_any_call("Ingestion pipeline completed successfully")
                        assert mock_log.call_count > 0 # Ensure audit events were logged