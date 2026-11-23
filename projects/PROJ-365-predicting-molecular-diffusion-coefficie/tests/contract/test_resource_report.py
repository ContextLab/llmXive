import json
from pathlib import Path

def test_resource_summary_fields():
    """
    Contract test for the aggregated resource summary report.

    The pipeline should generate ``artifacts/reports/resource_summary.json``
    containing at least the following numeric fields:
    - ``total_seconds``: total runtime in seconds
    - ``peak_memory_mb``: peak memory usage in megabytes
    """
    resource_path = Path("artifacts/reports/resource_summary.json")
    assert resource_path.is_file(), f"{resource_path} does not exist"

    with resource_path.open() as f:
        data = json.load(f)

    # Verify required keys exist
    for key in ("total_seconds", "peak_memory_mb"):
        assert key in data, f"Missing key '{key}' in resource_summary.json"

        # Verify values are numeric (int or float)
        value = data[key]
        assert isinstance(value, (int, float)), (
            f"'{key}' should be numeric, got {type(value).__name__}"
        )