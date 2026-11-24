"""
Unit tests for the composition‑only graph builder.

The tests verify that:
  * Distinct formulas produce distinct graphs (different node feature
    matrices because the element fractions differ).
  * The graph is fully connected, including self‑loops.
  * Edge weights are symmetric (w(i, j) == w(j, i)).
  * A warning is emitted and ``None`` is returned for an unknown element.
"""

import logging

import pytest
import torch

from src.graphs.composition import build_composition_graph

@pytest.fixture
def caplog_debug(caplog):
    """Enable DEBUG level for the duration of a test."""
    caplog.set_level(logging.DEBUG)
    return caplog

def test_distinct_graphs():
    """FeO and Fe2O3 have the same element set but different fractions."""
    g_feo = build_composition_graph(
        material_id="m_feo",
        formula="FeO",
        band_gap=1.0,
        hardness=5.0,
        cache=False,
    )
    g_fe2o3 = build_composition_graph(
        material_id="m_fe2o3",
        formula="Fe2O3",
        band_gap=2.0,
        hardness=6.0,
        cache=False,
    )

    # Both graphs should have two nodes (Fe, O)
    assert g_feo.num_nodes == 2
    assert g_fe2o3.num_nodes == 2

    # Node feature matrices must differ because the fractions differ
    assert not torch.allclose(g_feo.x, g_fe2o3.x)

def test_self_loops_and_symmetry():
    """Fully‑connected clique (including self‑loops) and symmetric weights."""
    g = build_composition_graph(
        material_id="m_test",
        formula="FeO",
        band_gap=1.0,
        hardness=5.0,
        cache=False,
    )
    n = g.num_nodes
    # Expected number of edges = N^2 (self‑loops included)
    assert g.edge_index.shape[1] == n * n

    # Check that self‑loops are present
    self_loops = (g.edge_index[0] == g.edge_index[1]).nonzero(as_tuple=False).squeeze()
    assert self_loops.numel() == n  # one self‑loop per node

    # Edge weights must be symmetric
    # Build a lookup dict {(i,j): weight}
    weights = {}
    for src, dst, w in zip(g.edge_index[0].tolist(), g.edge_index[1].tolist(), g.edge_weight.tolist()):
        weights[(src, dst)] = w
    for (i, j), w in list(weights.items()):
        assert pytest.approx(w, rel=1e-6) == weights.get((j, i), None)

def test_unknown_element_warning(caplog_debug):
    """A formula with an unknown element should emit a warning and return None."""
    result = build_composition_graph(
        material_id="m_unknown",
        formula="FakeX",  # X is not a real element
        band_gap=0.0,
        hardness=0.0,
        cache=False,
    )
    assert result is None
    # Verify that a warning was logged
    warnings = [rec for rec in caplog_debug.records if rec.levelno == logging.WARNING]
    assert any("Unknown element" in w.getMessage() for w in warnings), "Expected warning about unknown element"