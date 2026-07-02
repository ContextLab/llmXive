"""Test that the T015 script produces a correctly formatted CSV."""
import csv
from pathlib import Path

from t015_generate_full_results import run

def test_results_full_csv_written(tmp_path: Path):
    # Use a small number of games for speed in CI.
    out_dir = tmp_path / "results"
    csv_path = run(agents=3, games=10, output_dir=out_dir)

    # Basic existence & naming checks
    assert csv_path.is_file()
    assert csv_path.name == "results_full.csv"

    # Verify header and row count (including header)
    with csv_path.open(newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]
    # Expect exactly ``games`` data rows
    assert len(rows) == 11  # 10 games + header
    # Spot‑check a few values are convertible to float/int
    for row in rows[1:]:
        game_id = int(row[0])
        spec_idx = float(row[1])
        retrieval = float(row[2])
        context = row[3]
        agent_cnt = int(row[4])
        assert game_id >= 0
        assert spec_idx >= 0
        assert 0.0 <= retrieval <= 1.0
        assert context == "full"
        assert agent_cnt == 3