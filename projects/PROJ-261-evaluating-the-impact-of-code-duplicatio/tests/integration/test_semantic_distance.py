import csv
import pathlib

from code.model_metrics import compute_semantic_distance_batch, main

def test_semantic_distance_file_created(tmp_path, monkeypatch):
    """
    Run the model_metrics main entry‑point and verify that the semantic
    distance CSV is produced and contains at least one numeric entry.
    """
    # Ensure the output directory exists
    processed_dir = pathlib.Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create a minimal clone‑metrics CSV that the distance routine can read.
    input_path = processed_dir / "clone_metrics.csv"
    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["segment_id", "code"])
        writer.writeheader()
        writer.writerow({"segment_id": "seg1", "code": "def foo():\n    return 1"})
        writer.writerow({"segment_id": "seg2", "code": "def bar(x):\n    return x * 2"})

    # Run the main function which should compute both perplexity and semantic distance.
    main()

    output_path = processed_dir / "semantic_distance.csv"
    assert output_path.is_file(), "semantic_distance.csv was not created"

    # Verify the file has the expected columns and at least one valid numeric distance.
    with output_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows, "semantic_distance.csv is empty"
        for row in rows:
            assert "segment_id" in row and "semantic_distance" in row
            # The distance should be a float convertible string.
            try:
                float(row["semantic_distance"])
            except ValueError:
                raise AssertionError("semantic_distance is not a numeric value")