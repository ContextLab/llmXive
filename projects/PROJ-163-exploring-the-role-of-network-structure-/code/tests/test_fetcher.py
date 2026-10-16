"""
Unit tests for ``code.fetcher``.

The tests mock the IBM Quantum service and verify:
* schema conformance of a fabricated raw JSON snapshot,
* exponential back‑off behaviour,
* proper handling of HTTP 429 rate‑limit responses,
* exclusion of stale calibration data (>30 days),
* that the fetcher raises ``RuntimeError`` when the service cannot be initialised.
"""
import json
import builtins
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from jsonschema import validate, ValidationError

# Import the module under test
from code import fetcher

# Load the raw calibration schema for validation
with open(
    "specs/001-exploring-the-role-of-network-structure/contracts/raw_calibration.schema.yaml",
    "r",
    encoding="utf-8",
) as f:
    RAW_SCHEMA = json.load(f)


def make_fake_properties(fresh: bool = True):
    """
    Build a minimal mock object that mimics ``BackendProperties``.
    """
    class Param:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    class Gate:
        def __init__(self):
            self.gate = "cx"
            self.parameters = [Param("gate_error", 0.01), Param("readout_error", 0.02)]

    class QubitProp:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    class BackendProperties:
        def __init__(self):
            self.coupling_map = [[0, 1], [1, 2]]
            self.qubits = [
                [QubitProp("T1", 150e-6), QubitProp("T2", 100e-6)],
                [QubitProp("T1", 160e-6), QubitProp("T2", 110e-6)],
                [QubitProp("T1", 155e-6), QubitProp("T2", 105e-6)],
            ]
            self.gates = [Gate()]
            now = datetime.now(timezone.utc)
            self.last_update_date = now if fresh else now - timedelta(days=31)

        def to_dict(self):
            # Simple serialisable representation matching the schema
            return {
                "device_id": "fake_backend",
                "timestamp": self.last_update_date.isoformat(),
                "coupling_map": self.coupling_map,
                "properties": {
                    "qubits": [
                        [{"name": "T1", "value": 150e-6}, {"name": "T2", "value": 100e-6}],
                        [{"name": "T1", "value": 160e-6}, {"name": "T2", "value": 110e-6}],
                        [{"name": "T1", "value": 155e-6}, {"name": "T2", "value": 105e-6}],
                    ],
                    "gates": [
                        {
                            "gate": "cx",
                            "parameters": [
                                {"name": "gate_error", "value": 0.01},
                                {"name": "readout_error", "value": 0.02},
                            ],
                        }
                    ],
                },
            }

    return BackendProperties()


def test_schema_conformance():
    """A correctly‑structured snapshot must validate against the contract."""
    props = make_fake_properties()
    raw_dict = props.to_dict()
    # ``validate`` raises ``ValidationError`` on failure.
    validate(instance=raw_dict, schema=RAW_SCHEMA)


def test_exponential_backoff_success():
    """The retry helper should succeed after transient failures."""
    call_counter = {"count": 0}

    def flaky():
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            raise ConnectionError("temporary network glitch")
        return "ok"

    result = fetcher.retry_with_exponential_backoff(flaky, max_attempts=5, base_delay=0.01)
    assert result == "ok"
    assert call_counter["count"] == 3


def test_exponential_backoff_failure():
    """After the maximum attempts the original exception must be raised."""
    with pytest.raises(ConnectionError):
        fetcher.retry_with_exponential_backoff(
            lambda: (_ for _ in ()).throw(ConnectionError("permanent failure")),
            max_attempts=3,
            base_delay=0.01,
        )


def test_rate_limit_handler():
    """A 429 response should trigger a sleep and return True."""
    mock_resp = mock.Mock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "0"}  # no actual wait in test
    with mock.patch("time.sleep") as mock_sleep:
        handled = fetcher.rate_limit_handler(mock_resp)
        mock_sleep.assert_called_once_with(0)
        assert handled is True

    # Non‑429 should be a no‑op
    mock_resp.status_code = 200
    with mock.patch("time.sleep") as mock_sleep:
        handled = fetcher.rate_limit_handler(mock_resp)
        mock_sleep.assert_not_called()
        assert handled is False


def test_validate_data_freshness():
    fresh_props = make_fake_properties(fresh=True)
    stale_props = make_fake_properties(fresh=False)

    assert fetcher.validate_data_freshness(fresh_props) is True
    assert fetcher.validate_data_freshness(stale_props) is False


def test_fetcher_raises_on_missing_token(monkeypatch):
    """If ``IBMQ_TOKEN`` is not set, initialisation must raise RuntimeError."""
    # Ensure environment variable is absent
    monkeypatch.delenv("IBMQ_TOKEN", raising=False)

    # Mock ``load_config`` to return an object without a token attribute
    class DummyConfig(dict):
        pass

    monkeypatch.setattr(fetcher, "load_config", lambda: DummyConfig())
    with pytest.raises(RuntimeError, match="IBMQ_TOKEN not found"):
        fetcher._init_service()


def test_fetch_all_backends_total_failure(monkeypatch):
    """
    Simulate a scenario where every backend fetch fails – the orchestrator
    must raise ``RuntimeError`` because no snapshots can be saved.
    """
    # Mock service that reports a single backend
    dummy_backend = mock.Mock()
    dummy_backend.name = "bad_backend"
    dummy_backend.operational = True

    dummy_service = mock.Mock()
    dummy_service.backends.return_value = [dummy_backend]

    # Force ``fetch_backend_properties`` to raise for this backend
    def failing_fetch(name):
        raise RuntimeError("simulated fetch failure")

    monkeypatch.setattr(fetcher, "_init_service", lambda: dummy_service)
    monkeypatch.setattr(fetcher, "fetch_backend_properties", failing_fetch)

    # ``save_backend_snapshot`` should never be called
    monkeypatch.setattr(fetcher, "save_backend_snapshot", lambda *a, **k: None)

    with pytest.raises(RuntimeError, match="No backend snapshots were saved"):
        fetcher.fetch_and_save_snapshots()
