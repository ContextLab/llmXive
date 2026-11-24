import importlib.util
import pathlib
import pandas as pd
import numpy as np
import requests
import time
from unittest import mock

def _load_data_ingestion_module():
    """
    Dynamically load the `01_data_ingestion.py` module which has a
    non‑standard filename (starts with a digit). This avoids import
    syntax errors while still giving access to its public functions.
    """
    module_path = (
        pathlib.Path(__file__).resolve()
        .parents[2]  # project root /code/tests/ -> project root
        / "code"
        / "01_data_ingestion.py"
    )
    spec = importlib.util.spec_from_file_location("data_ingestion", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, f"Cannot load module from {module_path}"
    spec.loader.exec_module(module)
    return module


def test_standardize_affinity_value_logk():
    mod = _load_data_ingestion_module()
    # Direct logK should be returned unchanged
    assert mod.standardize_affinity_value(2.5, "logK") == 2.5
    assert mod.standardize_affinity_value(2.5, "log_k") == 2.5
    assert mod.standardize_affinity_value(2.5, "log") == 2.5


def test_standardize_affinity_value_dg():
    mod = _load_data_ingestion_module()
    # ΔG (kcal/mol) converted to log K using the constant 1.364
    dg = -5.0
    expected = -dg / 1.364
    result = mod.standardize_affinity_value(dg, "kcal/mol")
    assert np.isclose(result, expected, atol=1e-6)


def test_extract_halide_identity():
    mod = _load_data_ingestion_module()
    # Various textual patterns should map to the correct halide symbol
    assert mod.extract_halide_identity({"desc": "fluoride"}) == "F"
    assert mod.extract_halide_identity({"desc": "Cl-"}) == "Cl"
    assert mod.extract_halide_identity({"desc": "bromide"}) == "Br"
    assert mod.extract_halide_identity({"desc": "iodide"}) == "I"
    # Unknown patterns return None
    assert mod.extract_halide_identity({"desc": "unknown"}) is None


def test_validate_and_clean_duplicate_averaging():
    mod = _load_data_ingestion_module()
    # Create a small DataFrame with two identical host‑halide rows but differing values
    raw_df = pd.DataFrame(
        [
            {
                "host_id": "H1",
                "smiles": "C",
                "halide_info": "fluoride",
                "solvent": "acetonitrile",
                "source": "test",
                "value": 1.0,
                "unit": "logK",
            },
            {
                "host_id": "H1",
                "smiles": "C",
                "halide_info": "fluoride",
                "solvent": "acetonitrile",
                "source": "test",
                "value": 3.0,
                "unit": "logK",
            },
        ]
    )
    cleaned = mod.validate_and_clean_data(raw_df)
    # After aggregation we expect a single row with the mean binding constant (2.0)
    assert len(cleaned) == 1
    row = cleaned.iloc[0]
    assert row["host_id"] == "H1"
    assert row["halide_identity"] == "F"
    assert np.isclose(row["binding_constant"], 2.0, atol=1e-6)


def test_filter_hosts_with_multiple_halides():
    mod = _load_data_ingestion_module()
    # Construct a DataFrame where host H1 has three halides, H2 only two
    df = pd.DataFrame(
        [
            {"host_id": "H1", "halide_identity": "F"},
            {"host_id": "H1", "halide_identity": "Cl"},
            {"host_id": "H1", "halide_identity": "Br"},
            {"host_id": "H2", "halide_identity": "F"},
            {"host_id": "H2", "halide_identity": "Cl"},
        ]
    )
    filtered = mod.filter_hosts_with_multiple_halides(df)
    # Only host H1 should be retained
    assert set(filtered["host_id"].unique()) == {"H1"}
    assert len(filtered) == 3  # three halide rows for H1


def test_fetch_outcome_records_error_handling(monkeypatch):
    """
    Simulate a HTTP 404 response for both PubChem and NIST to verify that
    the outcome JSON records the real status code and does not treat the
    situation as a silent success.
    """
    import requests

    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.text = ""
        def json(self):
            return {}
        def raise_for_status(self):
            raise requests.HTTPError(response=self)

    def mock_get(url, timeout=10):
        # Return a 404 for any URL
        return MockResponse(404)

    # Patch network calls and sleep to keep the test fast
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    mod = _load_data_ingestion_module()
    result = mod.build_raw_records()
    outcome = result["outcome"]

    # Both sources should have recorded a 404 status and zero records
    for source in ("pubchem", "nist"):
        for halide in ("fluoride", "chloride", "bromide", "iodide"):
            halide_out = outcome[source]["halides"][halide]
            assert halide_out["status"] == 404
            assert halide_out["records_fetched"] == 0
            assert halide_out["retries_exhausted"] is False