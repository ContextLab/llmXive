"""Simple integration test for the summary generation script.

The test executes the script and checks that the expected output file
``results/summary.md`` exists and contains the required section headers.
"""

import subprocess
import sys
from pathlib import Path

def test_summary_generation(tmp_path: Path) -> None:
    # Ensure we run from the repository root
    repo_root = Path(__file__).resolve().parents[2]

    # Create minimal placeholder result files so the script can run.
    results_dir = repo_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # metrics.csv with two seeds
    (results_dir / "metrics.csv").write_text(
        "seed,mae,rmse\n"
        "0,0.1234,0.2345\n"
        "1,0.1300,0.2400\n",
        encoding="utf-8",
    )

    # attributions.json
    (results_dir / "attributions.json").write_text(
        '{"feature_A": 0.8, "feature_B": 0.5, "feature_C": 0.2}', encoding="utf-8"
    )

    # significance.csv
    (results_dir / "significance.csv").write_text(
        "test,metric,p_value\n"
        "paired_t,mae,0.03\n"
        "paired_t,rmse,0.07\n",
        encoding="utf-8",
    )

    # Run the summary script
    script_path = repo_root / "code" / "generate_summary.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    # The script should exit cleanly
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    summary_path = results_dir / "summary.md"
    assert summary_path.is_file(), "summary.md was not created"

    content = summary_path.read_text(encoding="utf-8")
    # Basic sanity checks for section headers
    for header in [
        "# Final Results Summary",
        "## 1. Per‑seed Metrics",
        "## 2. Overall Statistics",
        "## 3. Feature Attribution (Top 10)",
        "## 4. Statistical Significance Tests",
        "## 5. Generated Visualisations",
    ]:
        assert header in content, f"Missing header {header}"