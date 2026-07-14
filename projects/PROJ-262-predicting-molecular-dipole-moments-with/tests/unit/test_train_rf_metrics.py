import csv
import os
import tempfile

from training.train_rf import write_metrics_csv

def test_write_metrics_csv_creates_file_and_variance():
    # Prepare a small deterministic metrics list
    metrics = [
        {"seed": 42, "model": "random_forest", "mae": 0.123456, "rmse": 0.234567},
        {"seed": 43, "model": "random_forest", "mae": 0.223456, "rmse": 0.334567},
        {"seed": 44, "model": "random_forest", "mae": 0.323456, "rmse": 0.434567},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "metrics.csv")
        write_metrics_csv(metrics, out_path)

        # Verify file exists
        assert os.path.isfile(out_path)

        # Verify CSV content and that variance appears only on the first row
        with open(out_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        # Compute expected variance manually
        rmse_vals = [m["rmse"] for m in metrics]
        expected_variance = sum((x - sum(rmse_vals) / len(rmse_vals)) ** 2 for x in rmse_vals) / len(rmse_vals)

        # First row should contain variance
        assert float(rows[0]["rmse_variance"]) == pytest.approx(expected_variance, rel=1e-6)
        # Subsequent rows should have empty variance field
        assert rows[1]["rmse_variance"] == ""
        assert rows[2]["rmse_variance"] == ""