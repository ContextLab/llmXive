import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, MagicMock
from src.services.ingest import fetch_sample_ids, fetch_and_build_subgraph
from src.lib import config

def test_ingest_creates_subgraph():
    """
    Integration test: Verify that the ingestion pipeline successfully
    fetches data and constructs a networkx.Graph object.
    """
    # Mock the OpenAlex API to avoid network dependency in CI
    mock_work = MagicMock()
    mock_work.id = "https://openalex.org/W123456"
    mock_work.title = "Test Paper"
    mock_work.cited_by_count = 10
    mock_work.referenced_works = ["https://openalex.org/W789012"]

    mock_work_2 = MagicMock()
    mock_work_2.id = "https://openalex.org/W789012"
    mock_work_2.title = "Referenced Paper"
    mock_work_2.cited_by_count = 5
    mock_work_2.referenced_works = []

    with patch('src.services.ingest.Works') as mock_works_class:
        # Setup the mock to return our fake works
        mock_instance = MagicMock()
        mock_instance.sample.return_value = [mock_work, mock_work_2]
        mock_instance.filter.return_value = [mock_work, mock_work_2]
        mock_works_class.return_value = mock_instance

        # Run the ingestion logic
        # 1. Fetch IDs (mocked)
        ids = fetch_sample_ids(target_size=2, seed=42)
        
        # 2. Build Graph (mocked)
        G = fetch_and_build_subgraph(ids, depth=1)

        # Assertions
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() >= 0

        # Check node attributes
        for node_id, data in G.nodes(data=True):
            assert 'title' in data
            assert 'citation_count' in data
            assert 'primary_cluster' in data
            assert 'topic_cluster' in data
            assert data['primary_cluster'] is None # Not clustered yet
            assert data['topic_cluster'] is None

        # Check edge connectivity
        # We expect an edge between W123456 and W789012
        assert G.has_edge("123456", "789012") or G.has_edge("123456", "W789012") # Depending on ID parsing

def test_ingest_handles_empty_response():
    """
    Test that the pipeline handles an empty API response gracefully.
    """
    with patch('src.services.ingest.Works') as mock_works_class:
        mock_instance = MagicMock()
        mock_instance.sample.return_value = []
        mock_instance.filter.return_value = []
        mock_works_class.return_value = mock_instance

        ids = fetch_sample_ids(target_size=10, seed=42)
        assert len(ids) == 0

        G = fetch_and_build_subgraph(ids, depth=1)
        assert G.number_of_nodes() == 0
