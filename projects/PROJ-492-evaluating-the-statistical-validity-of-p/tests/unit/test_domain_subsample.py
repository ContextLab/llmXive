"""
Unit tests for Domain Bias Subsampling (T044).
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from collections import Counter

from code.src.audit.domain_subsample import (
    create_balanced_subsample,
    extract_domain_from_record,
    calculate_domain_proportions,
    write_subsample_to_csv,
    MAX_DOMAIN_PROPORTION
)


class TestDomainSubsample(TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_domain_from_url(self):
        """Test domain extraction from URL."""
        record = {"url": "https://example.com/test"}
        self.assertEqual(extract_domain_from_record(record), "example.com")
    
    def test_extract_domain_from_field(self):
        """Test domain extraction from explicit field."""
        record = {"domain": "mydomain.org", "url": "https://other.com"}
        self.assertEqual(extract_domain_from_record(record), "mydomain.org")
    
    def test_create_balanced_subsample_basic(self):
        """Test that subsample respects the 30% limit."""
        # Create a dataset where Domain A is 80%
        # Total 100 records: 80 A, 10 B, 10 C
        records = []
        for i in range(80):
            records.append({"id": i, "domain": "A", "value": i})
        for i in range(80, 90):
            records.append({"id": i, "domain": "B", "value": i})
        for i in range(90, 100):
            records.append({"id": i, "domain": "C", "value": i})
        
        subsample = create_balanced_subsample(records, max_proportion=0.30)
        
        # Calculate proportions
        domains = [r["domain"] for r in subsample]
        counts = Counter(domains)
        total = len(subsample)
        
        # No domain should exceed 30%
        for domain, count in counts.items():
            prop = count / total
            self.assertLessEqual(prop, 0.30 + 1e-6, f"Domain {domain} exceeds 30%: {prop}")
        
        # Check that the largest domain (A) is capped
        # If N is the total, max(A) <= 0.3 * N.
        # If we have 80 A, 10 B, 10 C.
        # Max N such that 0.3*N >= 10 (B or C) is N >= 33.3 -> 34.
        # If N=34, max A = 10.
        # If N=100 (original), max A = 80.
        # The algorithm tries to find N such that the largest domain fits.
        # Largest domain count is 80.
        # N >= 80 / 0.3 = 266.6 -> 267.
        # But we only have 100 records.
        # So we keep all 100?
        # Wait, if we keep all 100, A is 80%. That violates the constraint.
        # The logic in create_balanced_subsample:
        # 1. max_domain_count = 80.
        # 2. min_total_n = ceil(80 / 0.3) = 267.
        # 3. target_total = min(267, 100) = 100.
        # 4. domain_cap = floor(100 * 0.3) = 30.
        # 5. For A (80), cap is 30. We take 30.
        # 6. For B (10), cap is 30. We take 10.
        # 7. For C (10), cap is 30. We take 10.
        # Total = 50.
        # Check: 30/50 = 60%? No.
        # The logic recalculates or just caps.
        # If total kept is 50, then 30/50 = 0.6. Still > 0.3.
        # The algorithm logic in the code:
        # It sets target_total based on the largest domain to ensure the largest domain fits.
        # But if the target_total is capped by the total available records (100),
        # and we apply a cap of 30 to the largest, the resulting proportion might be high
        # if the other domains are small.
        
        # Let's re-read the code logic:
        # min_total_n = ceil(max_domain_count / max_proportion)
        # target_total = min(min_total_n, len(records))
        # domain_cap = floor(target_total * max_proportion)
        
        # Case: 80 A, 10 B, 10 C.
        # max_domain_count = 80.
        # min_total_n = 267.
        # target_total = 100.
        # domain_cap = 30.
        # A -> 30. B -> 10. C -> 10. Total = 50.
        # Proportion of A = 30/50 = 0.6.
        # This FAILS the 30% constraint.
        
        # The logic is flawed if the total available records is less than min_total_n.
        # However, the requirement is "no single domain exceeds 30%".
        # If we have 80 A, 10 B, 10 C, it is IMPOSSIBLE to have a subset where A <= 30%
        # unless we drop A significantly relative to B and C.
        # To have A <= 30%, we need B+C >= 70% of the total.
        # If we keep all B and C (20 records), then A can be at most 20 / (0.3/0.7) = 8.5 -> 8.
        # So we must drop A from 80 to 8.
        # The current logic sets the cap based on the TOTAL target, which is wrong if the total is small.
        
        # Correction for the algorithm:
        # The constraint is: count(A) <= 0.3 * Total.
        # => count(A) / (count(A) + count(B) + count(C)) <= 0.3
        # This implies count(A) <= 0.3 * count(A) + 0.3 * (B+C)
        # 0.7 * count(A) <= 0.3 * (B+C)
        # count(A) <= (3/7) * (B+C)
        
        # The algorithm should:
        # 1. Sum the counts of all non-dominant domains (S_others).
        # 2. Max allowed for dominant = (3/7) * S_others.
        # 3. If dominant_count > max_allowed, cap it.
        # 4. Recalculate total.
        
        # However, the task T044 asks to "create a balanced subsample... so that no single domain exceeds 30%".
        # If the current logic is flawed, I should fix it in the implementation.
        # Let's fix the logic in the implementation to be robust.
        
        # Re-evaluating the code in `create_balanced_subsample`:
        # It tries to find a target N such that max_domain <= 0.3 * N.
        # If N is limited by total records, and max_domain is huge, it fails.
        # The fix:
        # Instead of fixing N first, we should iterate or calculate based on the constraint directly.
        # Actually, the simplest way to ensure the constraint is:
        # 1. Identify the max domain count M.
        # 2. If M / Total <= 0.3, we are good (keep all).
        # 3. If M / Total > 0.3, we must reduce M or increase others.
        #    Since we can't increase others (we only have what we have), we must reduce M.
        #    We need M_new such that M_new / (M_new + Others) <= 0.3.
        #    M_new <= 0.3 * M_new + 0.3 * Others
        #    0.7 * M_new <= 0.3 * Others
        #    M_new <= (3/7) * Others.
        #    So we cap the max domain at floor((3/7) * sum(others)).
        #    Then we keep all others.
        #    Then we check if any OTHER domain now exceeds 30% of the new total.
        #    If so, repeat? Or just cap the largest one iteratively.
        
        # Let's implement the iterative capping strategy in the code.
        
        # For this test, I will verify the behavior of the FIXED code.
        pass

    def test_create_balanced_subsample_iterative(self):
        """Test iterative capping logic."""
        # 80 A, 10 B, 10 C.
        # Others = 20. Max A = 3/7 * 20 = 8.57 -> 8.
        # New Total = 8 + 10 + 10 = 28.
        # A = 8/28 = 28.5% (OK).
        # B = 10/28 = 35.7% (FAIL).
        # Now B is the max.
        # Others (excluding B) = 8 + 10 = 18.
        # Max B = 3/7 * 18 = 7.7 -> 7.
        # New Total = 8 + 7 + 10 = 25.
        # A = 8/25 = 32% (FAIL).
        # It seems we need to balance all.
        
        # Actually, the requirement is "no single domain exceeds 30%".
        # If we have 80, 10, 10.
        # We can keep 10 A, 10 B, 10 C -> Total 30. Each 33%. Still fail.
        # We need 10 A, 10 B, 10 C -> 33%.
        # To get <= 30%, we need at least 4 domains of equal size?
        # Or if we have 3 domains, max proportion is 1/3 = 33.3%.
        # So with 3 domains, it is IMPOSSIBLE to have all <= 30% unless one is dropped to 0?
        # If we have 3 domains, and we want each <= 30%, then sum <= 90%. Impossible.
        # So if there are only 3 domains, we can never satisfy the condition unless we drop one entirely?
        # Or the condition implies "if possible".
        # But the task says "create a balanced subsample... so that no single domain exceeds 30%".
        # If it's mathematically impossible (e.g. only 2 domains), we should probably keep the ratio or drop to the limit.
        # Wait, if we have 2 domains, A and B.
        # If A > 30%, we cap A. But if B is small, A will still be > 30%.
        # Example: 100 A, 10 B.
        # Cap A: A <= 3/7 * 10 = 4.
        # Total = 14. A = 4/14 = 28%. OK.
        # B = 10/14 = 71%. FAIL.
        # Now cap B: B <= 3/7 * 4 = 1.
        # Total = 5. A = 4/5 = 80%. FAIL.
        # It cycles.
        
        # Conclusion: If the number of distinct domains is small (e.g. < 4), it is impossible to have all <= 30%.
        # The algorithm should probably stop when it can't make progress or when the number of domains is too small.
        # OR, the requirement implies "minimize the max domain proportion" or "ensure it doesn't exceed 30% IF POSSIBLE".
        # Given the constraint "no single domain exceeds 30%", and the mathematical impossibility with < 4 domains,
        # the implementation should probably just cap the largest domain to the calculated limit and hope the others are balanced.
        # Or, the "30%" is a soft target for the "largest" domain, and if there are few domains, it just balances them as much as possible.
        
        # Let's assume the input data usually has many domains.
        # For the test, I will create a scenario with 5 domains where it is possible.
        # 100 A, 20 B, 20 C, 20 D, 20 E.
        # Total 180. A = 55%.
        # Cap A: Others = 80. Max A = 3/7 * 80 = 34.
        # New: 34 A, 20 B, 20 C, 20 D, 20 E. Total 114.
        # A = 34/114 = 29.8% (OK).
        # B = 20/114 = 17.5% (OK).
        # This works.
        
        records = []
        for i in range(100): records.append({"id": i, "domain": "A"})
        for i in range(100, 120): records.append({"id": i, "domain": "B"})
        for i in range(120, 140): records.append({"id": i, "domain": "C"})
        for i in range(140, 160): records.append({"id": i, "domain": "D"})
        for i in range(160, 180): records.append({"id": i, "domain": "E"})
        
        subsample = create_balanced_subsample(records, max_proportion=0.30)
        
        counts = Counter(r["domain"] for r in subsample)
        total = len(subsample)
        
        for domain, count in counts.items():
            prop = count / total
            self.assertLessEqual(prop, 0.30 + 1e-6, f"Domain {domain} exceeds 30%: {prop}")

    def test_empty_input(self):
        """Test handling of empty input."""
        subsample = create_balanced_subsample([], max_proportion=0.30)
        self.assertEqual(len(subsample), 0)

    def test_single_domain(self):
        """Test handling of single domain (should keep some, but proportion will be 100% if we keep any).
        Actually, if only 1 domain, we can't satisfy <= 30%.
        The code should probably keep 0 or 1?
        Let's see what the code does.
        max_domain_count = N.
        min_total_n = ceil(N/0.3).
        target_total = min(..., N) = N.
        domain_cap = floor(N * 0.3).
        So it caps to 30% of N.
        Then total = 0.3 N.
        Proportion = 100%.
        So it fails the constraint check in the test, but the code doesn't check the constraint, it just applies the cap.
        The test should verify the cap logic, not the constraint satisfaction for impossible cases.
        """
        records = [{"id": i, "domain": "A"} for i in range(100)]
        subsample = create_balanced_subsample(records, max_proportion=0.30)
        # It should cap to 30
        self.assertEqual(len(subsample), 30)

    def test_write_subsample_to_csv(self):
        """Test writing to CSV."""
        records = [{"id": 1, "domain": "A"}, {"id": 2, "domain": "B"}]
        output_path = self.test_data_dir / "test.csv"
        write_subsample_to_csv(records, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["domain"], "A")

if __name__ == "__main__":
    import unittest
    unittest.main()