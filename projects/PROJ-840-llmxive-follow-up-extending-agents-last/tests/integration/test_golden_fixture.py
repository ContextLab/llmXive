import subprocess
import json
from pathlib import Path
import hashlib

def test_generate_and_verify_golden_fixture():
    """
    Executes the golden fixture generator and verifies the resulting artifact.

    Steps:
    1. Run the generator script via the module entry point.
    2. Ensure the output JSON file exists and is non‑empty.
    3. Validate that every record's ``ground_truth_label`` is one of the allowed
       labels and that the distribution matches the specification
       (5 State Persistence Errors, 5 Reasoning Deficits).
    4. Compute the SHA‑256 checksum of the generated file and compare it to the
       checksum recorded in ``data/processed/golden_fixture_checksum.txt``.
    """
    # Define expected paths
    output_path = Path("data/raw/golden_fixture.json")
    checksum_path = Path("data/processed/golden_fixture_checksum.txt")

    # Clean any previous artifacts to guarantee a fresh run
    if output_path.exists():
        output_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()

    # Run the generator script
    result = subprocess.run(
        [
            "python",
            "-m",
            "code.data.generator",
            "--seed",
            "42",
            "--num-tasks",
            "10",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    # Ensure the script exited cleanly
    assert result.returncode == 0, f"Generator failed: {result.stderr}"

    # Verify the output file exists and is non‑empty
    assert output_path.exists(), "Golden fixture JSON was not created."
    assert output_path.stat().st_size > 0, "Golden fixture JSON is empty."

    # Load and inspect the JSON content
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list), "Golden fixture should be a list of records."
    allowed_labels = {"State Persistence Error", "Reasoning Deficit", "Pass"}
    label_counts = {label: 0 for label in allowed_labels}

    for record in data:
        label = record.get("ground_truth_label")
        assert label in allowed_labels, f"Unexpected label: {label}"
        label_counts[label] = label_counts.get(label, 0) + 1

    # Required distribution: exactly 5 of each error type
    assert (
        label_counts["State Persistence Error"] == 5
    ), f"Expected 5 State Persistence Errors, found {label_counts['State Persistence Error']}"
    assert (
        label_counts["Reasoning Deficit"] == 5
    ), f"Expected 5 Reasoning Deficits, found {label_counts['Reasoning Deficit']}"

    # Verify checksum file exists and matches the computed checksum
    assert checksum_path.exists(), "Checksum file was not created."

    with open(output_path, "rb") as f:
        computed_checksum = hashlib.sha256(f.read()).hexdigest()

    with open(checksum_path, "r", encoding="utf-8") as f:
        recorded_checksum = f.read().strip()

    assert (
        computed_checksum == recorded_checksum
    ), "Checksum mismatch between computed and recorded values."