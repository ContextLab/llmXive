"""
Unit tests for the HEA data acquisition script.

The tests verify that:
1. A row missing the required ``yield_strength`` field raises ``ValueError``.
2. When provided with a valid CSV (served via a temporary HTTP server), the script
   writes ``data/raw/heas_raw.csv`` and the file conforms to the JSON‑schema.
"""

import os
import threading
import http.server
import socketserver
import tempfile
import pathlib
import json

import pytest

from code.data.fetch_heas import fetch_heas, _load_schema

@pytest.fixture
def temporary_http_server():
    """Start a simple HTTP server that serves files from a temporary directory."""
    temp_dir = tempfile.TemporaryDirectory()
    handler = http.server.SimpleHTTPRequestHandler
    # Change directory for the handler
    cwd = os.getcwd()
    os.chdir(temp_dir.name)

    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
            thread.join()
            os.chdir(cwd)
            temp_dir.cleanup()

def write_csv(path: pathlib.Path, rows: list[dict]):
    """Utility to write a minimal CSV file with the required columns."""
    header = ["alloy_id", "composition", "yield_strength", "phase", "temperature"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def test_missing_yield_strength_raises():
    """A CSV line missing ``yield_strength`` must trigger a ValueError."""
    # Create a temporary CSV file missing the column
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tf:
        tf.write(
            "alloy_id,composition,phase,temperature\n"
            "A1,\"{\\\"Fe\\\":0.5,\\\"Ni\\\":0.5}\",single,300\n"
        )
        tf.flush()
        os.environ["ZENODO_URL"] = f"file://{tf.name}"
        with pytest.raises(ValueError, match="Missing required columns"):
            fetch_heas()
        os.unlink(tf.name)

def test_successful_fetch_writes_file(temporary_http_server):
    """When a valid CSV is served, the script should download and write it."""
    # Prepare a valid CSV in the server's directory
    csv_content = (
        "alloy_id,composition,yield_strength,phase,temperature\\n"
        "A1,\"{\\\"Fe\\\":0.5,\\\"Ni\\\":0.5}\",200.0,single,300\\n"
        "A2,\"{\\\"Co\\\":0.3,\\\"Cr\\\":0.3,\\\"Mn\\\":0.4}\",250.0,single,300\\n"
    )
    csv_path = pathlib.Path("valid_dataset.csv")
    csv_path.write_text(csv_content, encoding="utf-8")

    # Point the script to the HTTP URL
    os.environ["ZENODO_URL"] = f"{temporary_http_server}/valid_dataset.csv"

    # Ensure any previous output is removed
    output_path = pathlib.Path("data/raw/heas_raw.csv")
    if output_path.is_file():
        output_path.unlink()

    # Run the fetch function
    result_path = fetch_heas()
    assert result_path == output_path
    assert output_path.is_file()

    # Load the written CSV and validate against the schema
    df = pd.read_csv(output_path)
    schema = _load_schema()
    for _, row in df.iterrows():
        # Convert composition JSON string back to dict for validation
        row_dict = row.to_dict()
        row_dict["composition"] = json.loads(row_dict["composition"])
        # jsonschema.validate will raise if the row is invalid
        validate(instance=row_dict, schema=schema)

    # Cleanup
    output_path.unlink()
    csv_path.unlink()