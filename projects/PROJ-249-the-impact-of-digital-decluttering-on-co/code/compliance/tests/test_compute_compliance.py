"""
Test suite for the compliance‑log pipeline implemented in
``code/compliance/compute_compliance.py``.

The tests cover:
  * Normal compliant / non‑compliant day calculation.
  * Detection of out‑of‑range minute values.
  * Detection of the extreme case where a participant reports 0 minutes for
    all 7 days (the ``zero_all_days`` flag).
"""

import csv
import json
from pathlib import Path
import tempfile

import pytest

# Import the function under test
from code.compliance.compute_compliance import run_compliance_pipeline


@pytest.fixture
def temp_compliance_dir():
    """
    Create a temporary directory containing three CSV log files that
    exercise the edge cases required by the specification:
    
      1. ``normal.csv`` – a participant with a mix of compliant and
         non‑compliant days, all minute values within the valid range.
      2. ``out_of_range.csv`` – a participant with a minute entry outside
         the allowed 0‑1440 range (negative value).
      3. ``zero_all.csv`` – a participant that reports 0 minutes for every
         day (the extreme case flag).
    
    Returns the path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Normal participant (P001)
        normal_path = base / "normal.csv"
        with normal_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "participant_id",
                    "date",
                    "social_media_minutes",
                    "news_consumption",
                    "notifications_off",
                    "is_compliant",
                    "notes",
                ],
            )
            writer.writeheader()
            # 3 compliant days (≤30 min, no news, notifications off)
            writer.writerow(
                {
                    "id": "P001_0",
                    "participant_id": "P001",
                    "date": "2024-01-01",
                    "social_media_minutes": "20",
                    "news_consumption": "False",
                    "notifications_off": "True",
                    "is_compliant": "True",
                    "notes": "",
                }
            )
            # 4 non‑compliant days
            writer.writerow(
                {
                    "id": "P001_1",
                    "participant_id": "P001",
                    "date": "2024-01-02",
                    "social_media_minutes": "100",
                    "news_consumption": "True",
                    "notifications_off": "False",
                    "is_compliant": "False",
                    "notes": "",
                }
            )
            writer.writerow(
                {
                    "id": "P001_2",
                    "participant_id": "P001",
                    "date": "2024-01-03",
                    "social_media_minutes": "45",
                    "news_consumption": "False",
                    "notifications_off": "True",
                    "is_compliant": "False",
                    "notes": "",
                }
            )

        # Out‑of‑range participant (P002)
        out_path = base / "out_of_range.csv"
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "participant_id",
                    "date",
                    "social_media_minutes",
                    "news_consumption",
                    "notifications_off",
                    "is_compliant",
                    "notes",
                ],
            )
            writer.writeheader()
            # Negative minutes (invalid)
            writer.writerow(
                {
                    "id": "P002_0",
                    "participant_id": "P002",
                    "date": "2024-01-01",
                    "social_media_minutes": "-10",
                    "news_consumption": "False",
                    "notifications_off": "True",
                    "is_compliant": "False",
                    "notes": "",
                }
            )
            # A normal day to ensure the participant is still processed
            writer.writerow(
                {
                    "id": "P002_1",
                    "participant_id": "P002",
                    "date": "2024-01-02",
                    "social_media_minutes": "15",
                    "news_consumption": "False",
                    "notifications_off": "True",
                    "is_compliant": "True",
                    "notes": "",
                }
            )

        # Zero‑all‑days participant (P003)
        zero_path = base / "zero_all.csv"
        with zero_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "participant_id",
                    "date",
                    "social_media_minutes",
                    "news_consumption",
                    "notifications_off",
                    "is_compliant",
                    "notes",
                ],
            )
            writer.writeheader()
            for i in range(7):
                writer.writerow(
                    {
                        "id": f"P003_{i}",
                        "participant_id": "P003",
                        "date": f"2024-01-{i+1:02d}",
                        "social_media_minutes": "0",
                        "news_consumption": "False",
                        "notifications_off": "True",
                        "is_compliant": "True",
                        "notes": "",
                    }
                )

        yield base  # provide the temporary directory to the test


def test_compliance_pipeline_normal_and_flags(temp_compliance_dir):
    """
    Run the compliance pipeline on the temporary data and verify:
    
    * The aggregated CSV contains the correct number of participants.
    * The ``minutes_out_of_range`` flag is set for P002.
    * The ``zero_all_days`` flag is set for P003.
    * Compliance percentages are computed correctly.
    """
    # Execute the pipeline, directing outputs to a temporary location
    with tempfile.TemporaryDirectory() as out_tmp:
        out_dir = Path(out_tmp)
        aggregated_csv = out_dir / "aggregated_compliance.csv"
        flags_json = out_dir / "compliance_flags.json"

        result = run_compliance_pipeline(
            raw_logs_dir=Path(temp_compliance_dir),
            aggregated_csv=aggregated_csv,
            flags_json=flags_json,
        )

        # ---- Verify aggregated CSV content ----
        assert aggregated_csv.exists(), "Aggregated CSV was not written"
        with aggregated_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Expect three participants (P001, P002, P003)
            participant_ids = {row["participant_id"] for row in rows}
            assert participant_ids == {"P001", "P002", "P003"}

            # Check compliance percentages
            # P001: 1 compliant day out of 3 → 33.3333%
            p001 = next(r for r in rows if r["participant_id"] == "P001")
            assert float(p001["compliance_percentage"]) == pytest.approx(33.3333, rel=1e-3)

            # P002: 1 compliant day out of 2 → 50%
            p002 = next(r for r in rows if r["participant_id"] == "P002")
            assert float(p002["compliance_percentage"]) == pytest.approx(50.0, rel=1e-3)

            # P003: all 7 days compliant (0 minutes meets the ≤30 rule) → 100%
            p003 = next(r for r in rows if r["participant_id"] == "P003")
            assert float(p003["compliance_percentage"]) == pytest.approx(100.0, rel=1e-3)

        # ---- Verify flags JSON content ----
        assert flags_json.exists(), "Flags JSON was not written"
        with flags_json.open(encoding="utf-8") as f:
            flags = json.load(f)

        # Expected flags per participant
        assert flags["P001"] == [], "P001 should have no flags"
        assert "minutes_out_of_range" in flags["P002"], "P002 should be flagged for out‑of‑range minutes"
        assert flags["P003"] == ["zero_all_days"], "P003 should be flagged for zero‑all‑days"

        # ---- Verify that the function returned matching in‑memory structures ----
        aggregated_mem = result["aggregated"]
        flags_mem = result["flags"]
        assert aggregated_mem["P001"]["compliant_days"] == 1
        assert "minutes_out_of_range" in flags_mem["P002"]
        assert flags_mem["P003"] == ["zero_all_days"]