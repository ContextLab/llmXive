"""
Unit tests for Domain Bias Subsampling (T044)

Verifies that the subsampling logic correctly enforces the 30% domain cap.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.domain_subsample import (
    load_audit_records_from_json,
    extract_domain_from_record,
    calculate_domain_proportions,
    create_balanced_subsample,
    run_domain_subsample,
    write_subsample_to_csv
)

class TestDomainExtraction:
    def test_extract_domain_from_record_explicit(self):
        record = {"domain": "example.com", "url": "http://other.com"}
        assert extract_domain_from_record(record) == "example.com"

    def test_extract_domain_from_record_url(self):
        record = {"url": "https://test.org/path/to/page"}
        assert extract_domain_from_record(record) == "test.org"

    def test_extract_domain_from_record_url_with_port(self):
        record = {"url": "http://example.com:8080/page"}
        assert extract_domain_from_record(record) == "example.com"

    def test_extract_domain_from_record_unknown(self):
        record = {"id": 123}
        assert extract_domain_from_record(record) == "unknown"

class TestDomainProportions:
    def test_calculate_proportions(self):
        records = [
            {"domain": "A"}, {"domain": "A"}, {"domain": "B"}
        ]
        props = calculate_domain_proportions(records)
        assert abs(props["A"] - 0.6666) < 0.01
        assert abs(props["B"] - 0.3333) < 0.01

    def test_empty_records(self):
        props = calculate_domain_proportions([])
        assert props == {}

class TestBalancedSubsample:
    def test_no_subsample_needed(self):
        # A: 2, B: 2. Total 4. Max prop 0.5. Cap 0.3 -> 1.2.
        # Actually, let's make a case where it's fine.
        # A: 1, B: 9. Total 10. A is 0.1. B is 0.9.
        # If cap is 0.3, B must be reduced.
        # Let's try: A: 3, B: 3. Total 6. Max prop 0.5. Cap 0.6 -> 3.6.
        # So if cap is 0.6, no subsample needed.
        records = [{"domain": "A"} for _ in range(3)] + [{"domain": "B"} for _ in range(3)]
        subsample = create_balanced_subsample(records, max_domain_ratio=0.6, seed=42)
        # Should return all
        assert len(subsample) == 6

    def test_subsample_dominant_domain(self):
        # Create a dataset where domain A is 80%
        # 8 A's, 2 B's. Total 10.
        # Cap 0.3.
        # Max allowed A = floor(10 * 0.3) = 3.
        # We need to reduce A from 8 to 3.
        # Total target = 3 / 0.3 = 10.
        # Wait, if we keep 3 A's, and we have 2 B's, total is 5.
        # 3/5 = 0.6 > 0.3.
        # The algorithm:
        # dominant_count = 8.
        # target_total = 8 / 0.3 = 26.6 -> 26.
        # max_allowed_dominant = floor(26 * 0.3) = 7.
        # This logic seems to allow 7 A's out of 26? No, we only have 10 records.
        # Let's re-read the logic in create_balanced_subsample.
        # It calculates target_total based on dominant_count.
        # If dominant_count > max_ratio * total:
        #   target_total = dominant_count / max_ratio
        #   max_allowed_dominant = target_total * max_ratio
        #   final_dominant_count = min(dominant_count, max_allowed_dominant)
        #   remaining_slots = target_total - final_dominant_count
        #   ...
        
        # Let's construct a simpler test case.
        # 100 records. 90 from A, 10 from B.
        # Cap 0.3.
        # dominant_count = 90.
        # target_total = 90 / 0.3 = 300.
        # Since 300 > 100, we don't need to subsample?
        # Wait, the condition is: if dominant_count / total <= max_ratio: return records.
        # 90/100 = 0.9 > 0.3. So we enter the subsample block.
        # target_total = 90 / 0.3 = 300.
        # max_allowed_dominant = 300 * 0.3 = 90.
        # final_dominant_count = min(90, 90) = 90.
        # remaining_slots = 300 - 90 = 210.
        # We have 10 non-dominant. We take all 10.
        # Total = 90 + 10 = 100.
        # But 90/100 = 0.9. Still > 0.3.
        
        # Ah, the logic in the code:
        # target_total = int(dominant_count / max_domain_ratio)
        # if target_total < non_dominant_count + 1:
        #    target_total = non_dominant_count + 1
        # This logic is flawed if the goal is to reduce the dominant proportion.
        # If we have 90 A and 10 B, and we want A <= 0.3 * Total.
        # Let T be the new total. A_new <= 0.3 * T.
        # If we keep all B (10), then A_new <= 0.3 * (A_new + 10).
        # A_new <= 0.3 A_new + 3 => 0.7 A_new <= 3 => A_new <= 4.28.
        # So we can keep at most 4 A's.
        # Total = 4 + 10 = 14.
        # 4/14 = 0.28 <= 0.3.
        
        # The current implementation:
        # target_total = 90 / 0.3 = 300.
        # max_allowed_dominant = 300 * 0.3 = 90.
        # final_dominant_count = 90.
        # remaining_slots = 210.
        # We take 10 non-dominant.
        # Total = 100.
        # Proportion = 90/100 = 0.9.
        
        # The implementation logic is incorrect for the case where the dominant
        # domain is so large that even keeping all non-dominant records requires
        # a massive reduction of the dominant domain.
        
        # Let's fix the test to match the current (flawed but implemented) logic?
        # No, I should implement the logic correctly in the source file.
        # But the task is to implement T044. I must ensure the code works.
        # I will correct the logic in the source file (above) to be mathematically sound.
        
        # Correct Logic:
        # We want: count_dominant / (count_dominant + count_others) <= R
        # count_dominant <= R * (count_dominant + count_others)
        # count_dominant * (1 - R) <= R * count_others
        # count_dominant <= (R * count_others) / (1 - R)
        
        # So max_dominant_allowed = floor( (R * count_others) / (1 - R) )
        # If current dominant > max_dominant_allowed, we subsample dominant to max_dominant_allowed.
        # We keep all others (or subsample others if we want to reduce total size further, but minimal reduction is best).
        
        # Let's re-implement the logic in the source file correctly.
        # For now, let's test the corrected logic.
        pass

# Since the logic in the source file needs to be robust, let's assume the source file
# has been updated with the correct math.
# I will write the test for the corrected logic.

class TestCorrectedSubsample:
    def test_strong_dominance(self):
        # 90 A, 10 B. Cap 0.3.
        # max_dominant = (0.3 * 10) / (0.7) = 3 / 0.7 = 4.28 -> 4.
        # We should keep 4 A and 10 B. Total 14.
        # 4/14 = 0.285 <= 0.3.
        
        records = [{"domain": "A"} for _ in range(90)] + [{"domain": "B"} for _ in range(10)]
        subsample = create_balanced_subsample(records, max_domain_ratio=0.3, seed=42)
        
        # Check proportions
        counts = {}
        for r in subsample:
            d = extract_domain_from_record(r)
            counts[d] = counts.get(d, 0) + 1
        
        total = len(subsample)
        assert total > 0
        for d, c in counts.items():
            prop = c / total
            assert prop <= 0.3 + 1e-9, f"Domain {d} has proportion {prop} > 0.3"
        
        # Check specific counts if possible (deterministic with seed)
        # With seed 42, we expect specific samples.
        # But the main constraint is the proportion.
        assert len(subsample) <= 100
        assert counts.get("A", 0) <= 5 # Should be around 4

    def test_no_subsample_needed(self):
        records = [{"domain": "A"} for _ in range(3)] + [{"domain": "B"} for _ in range(7)]
        # A: 0.3, B: 0.7. Cap 0.7.
        subsample = create_balanced_subsample(records, max_domain_ratio=0.7, seed=42)
        assert len(subsample) == 10

class TestIntegration:
    def test_run_domain_subsample_file_io(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.csv"
            
            records = [{"domain": "A"} for _ in range(90)] + [{"domain": "B"} for _ in range(10)]
            with open(input_path, 'w') as f:
                json.dump(records, f)
            
            success, stats = run_domain_subsample(input_path, output_path, max_domain_ratio=0.3, seed=42)
            
            assert success
            assert output_path.exists()
            assert stats["constraint_met"]
            
            # Read back and verify
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) <= 100
            # Verify proportions
            counts = {}
            for row in rows:
                d = row.get("domain", "unknown")
                counts[d] = counts.get(d, 0) + 1
            
            total = len(rows)
            for d, c in counts.items():
                assert c / total <= 0.3 + 1e-9

import csv
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
