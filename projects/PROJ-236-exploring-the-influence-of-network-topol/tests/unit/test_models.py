"""
Unit tests for the Pydantic models defined in ``code/utils/models.py``.

The test simply instantiates the models with valid data and verifies that
no ``pydantic.ValidationError`` is raised.
"""

import pytest

from utils.models import NetworkRealization, TransportResult


def test_network_realization_instantiation():
    """Instantiate ``NetworkRealization`` with a minimal valid example."""
    # A tiny 2‑node undirected graph with a single edge.
    adjacency = [
        [0, 1],
        [1, 0],
    ]

    nr = NetworkRealization(
        network_id="net_001",
        topology_type="small_world",
        cutoff=2.5,
        adjacency=adjacency,
    )

    assert isinstance(nr, NetworkRealization)
    assert nr.network_id == "net_001"
    assert nr.topology_type == "small_world"
    assert nr.cutoff == 2.5
    assert nr.adjacency == adjacency


def test_transport_result_instantiation():
    """Instantiate ``TransportResult`` with a minimal valid example."""
    tr = TransportResult(
        network_id="net_001",
        kappa=1.23,
        error_estimate=0.05,
        convergence_status=True,
        runtime=42.0,
        regime_flag="diffusive",
    )

    assert isinstance(tr, TransportResult)
    assert tr.network_id == "net_001"
    assert tr.kappa == 1.23
    assert tr.error_estimate == 0.05
    assert tr.convergence_status is True
    assert tr.runtime == 42.0
    assert tr.regime_flag == "diffusive"


def test_models_do_not_raise_validation_error():
    """A sanity check that the previous constructions raise no ValidationError."""
    # The constructions above already would raise if invalid; this simply
    # confirms that the imports and model definitions are functional.
    try:
        test_network_realization_instantiation()
        test_transport_result_instantiation()
    except Exception as exc:  # pragma: no cover
        pytest.fail(f"Model instantiation raised an unexpected exception: {exc}")