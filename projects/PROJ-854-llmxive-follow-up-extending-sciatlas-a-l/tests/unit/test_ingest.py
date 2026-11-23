import pytest
import networkx as nx
import numpy as np
from scipy import stats
from unittest.mock import patch
from src.services.ingest import validate_sampled_graph
from src.lib import config

def test_validate_sampled_graph_empty_graphs():
    """Test validation with an empty graph."""
    G = nx.Graph()
    result = validate_sampled_graph(G)
    assert result is False

def test_validate_sampled_graph_tolerance():
    """Test validation with a graph that barely passes the tolerance."""
    G = nx.erdos_renyi_graph(100, 0.05, seed=42)
    result = validate_sampled_graph(G)
    assert result is True

def test_validate_sampled_graph_output_format():
  """Test that the validation function generates the expected output."""
  G = nx.barabasi_albert_graph(100, 3, seed=42)
  result = validate_sampled_graph(G)
  assert result is True

  with open(config.get_artifacts_path() / "sampling_validation.json", "r") as f:
      data = json.load(f)
  assert "sampled_local_clustering_dist" in data
  assert "ks_statistic" in data
  assert "p_value" in data

def test_validate_sampled_graph_identical_graphs():
    """Test validation with identical graphs."""
    G1 = nx.barabasi_albert_graph(100, 3, seed=42)
    G2 = nx.barabasi_albert_graph(100, 3, seed=42)
    result = validate_sampled_graph(G1)
    assert result is True