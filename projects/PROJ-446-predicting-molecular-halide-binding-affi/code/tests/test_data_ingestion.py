import importlib.util
import pathlib
import json
import pandas as pd
import pytest

def _load_data_ingestion_module():
    """
    Dynamically load the `01_data_ingestion.py` module which has a
    non‑standard filename (starts with a digit). This resolves the module
    path robustly regardless of the repository nesting depth.
    """
    # Resolve a path that points to the project root where the `code` directory lives.
    current_path = pathlib.Path(__file__).resolve()
    # Walk up the directory tree until we find a folder that contains `code/01_data_ingestion.py`
    for parent in current_path.parents:
        candidate = parent / "code" / "01_data_ingestion.py"
        if candidate.is_file():
            module_path = candidate
            break
    else:
        raise FileNotFoundError("Unable to locate 01_data_ingestion.py in any parent directory.")

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
    assert pytest.approx(result, rel=1e-6) == expected

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
    assert pytest.approx(row["binding_constant"], rel=1e-6) == 2.0

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

def test_zero_records_path(monkeypatch, tmp_path):
    """
    Simulate a fetch that returns no records and ensure the pipeline
    creates the expected empty artifacts and exits cleanly.
    """
    mod = _load_data_ingestion_module()

    # Mock fetch functions to return empty results with a successful status.
    empty_outcome = {"status": 200, "records_fetched": 0, "retries_exhausted": False}
    monkeypatch.setattr(mod, "fetch_pubchem_records", lambda halide, max_retries=5, base_delay=2: ([], empty_outcome))
    monkeypatch.setattr(mod, "fetch_nist_records", lambda halide, max_retries=5, base_delay=2: ([], empty_outcome))

    # Run the data pipeline (the function handles empty data internally).
    mod.run_data_pipeline()

    # Verify that the four expected artifacts exist and are correctly formed.
    raw_path = tmp_path / "data" / "raw"
    # The function uses llmxive_toolkit.paths, which writes to the actual project
    # directory. We locate those files relative to the project root.
    from llmxive_toolkit import paths
    fetch_outcome_path = paths.data("raw", "fetch_outcome.json")
    cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")
    filtered_path = paths.data("raw", "filtered_hosts.csv")
    raw_json_path = paths.data("raw", "raw_scrape.json")

    for p in (fetch_outcome_path, cleaned_path, filtered_path, raw_json_path):
        assert p.is_file(), f"Expected artifact {p} to exist"

    # The cleaned and filtered CSVs should contain only headers (no data rows).
    cleaned_df = pd.read_csv(cleaned_path)
    filtered_df = pd.read_csv(filtered_path)
    assert cleaned_df.empty, "Cleaned CSV should have no data rows"
    assert filtered_df.empty, "Filtered CSV should have no data rows"

    # The fetch outcome JSON should record zero exclusions.
    with open(fetch_outcome_path, "r") as f:
        outcome = json.load(f)
    assert outcome.get("exclusions", None) == 0, "Exclusions count should be zero for empty fetch"