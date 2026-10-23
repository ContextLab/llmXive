import csv
from pathlib import Path

from code.window_index import DEFAULT_OUTPUT, generate_window_index

def test_window_index_row_count(tmp_path):
    output_path = tmp_path / "window_index.csv"
    generate_window_index(
        N=1_000_000,
        L_values=[1000, 10_000, 100_000],
        windows_per_L=100,
        seed=20231017,
        output_path=output_path,
    )
    with output_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 300
    # Ensure no overlapping windows for the same L
    for L in [1000, 10_000, 100_000]:
        starts = sorted(int(r["interval_start"]) for r in rows if int(r["interval_length"]) == L)
        for i in range(1, len(starts)):
            assert starts[i] >= starts[i-1] + L