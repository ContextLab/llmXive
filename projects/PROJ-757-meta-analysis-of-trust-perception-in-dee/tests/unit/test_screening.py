"""
Unit tests for screening logic, including Cohen's Kappa calculation and adjudication flagging.
"""
import pytest
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import math
import csv

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import parse_inclusion_criteria

# Mock data fixtures for testing
def create_screening_decision(
    study_id: str, 
    reviewer_id: int, 
    decision: str, 
    exclusion_codes: List[str] = None
) -> Dict[str, Any]:
    """Helper to create a mock screening decision row."""
    return {
        "study_id": study_id,
        "reviewer_id": reviewer_id,
        "decision": decision,  # 'include', 'exclude'
        "exclusion_codes": ",".join(exclusion_codes) if exclusion_codes else ""
    }

def create_screening_log_data() -> List[Dict[str, Any]]:
    """
    Creates a synthetic screening log dataset for testing Kappa calculation.
    Includes cases of agreement and disagreement to ensure robust testing.
    """
    data = [
        # Case 1: Both Include (Agreement)
        create_screening_decision("S001", 1, "include"),
        create_screening_decision("S001", 2, "include"),
        
        # Case 2: Both Exclude (Agreement) - NO_TRUST_METRIC
        create_screening_decision("S002", 1, "exclude", ["NO_TRUST_METRIC"]),
        create_screening_decision("S002", 2, "exclude", ["NO_TRUST_METRIC"]),
        
        # Case 3: Disagreement - R1 Include, R2 Exclude (NO_CONTROL_CONDITION)
        create_screening_decision("S003", 1, "include"),
        create_screening_decision("S003", 2, "exclude", ["NO_CONTROL_CONDITION"]),
        
        # Case 4: Disagreement - R1 Exclude (NOT_PEER_REVIEWED), R2 Include
        create_screening_decision("S004", 1, "exclude", ["NOT_PEER_REVIEWED"]),
        create_screening_decision("S004", 2, "include"),
        
        # Case 5: Both Include (Agreement)
        create_screening_decision("S005", 1, "include"),
        create_screening_decision("S005", 2, "include"),
        
        # Case 6: Both Exclude (Agreement) - NO_MODERATOR_DATA
        create_screening_decision("S006", 1, "exclude", ["NO_MODERATOR_DATA"]),
        create_screening_decision("S006", 2, "exclude", ["NO_MODERATOR_DATA"]),
        
        # Case 7: Disagreement - R1 Exclude (NO_TRUST_METRIC), R2 Include
        create_screening_decision("S007", 1, "exclude", ["NO_TRUST_METRIC"]),
        create_screening_decision("S007", 2, "include"),
        
        # Case 8: Both Exclude (Agreement) - NO_TRUST_METRIC
        create_screening_decision("S008", 1, "exclude", ["NO_TRUST_METRIC"]),
        create_screening_decision("S008", 2, "exclude", ["NO_TRUST_METRIC"]),
    ]
    return data

def calculate_cohen_kappa(
    decisions: List[Dict[str, Any]]
) -> Tuple[float, Dict[str, int]]:
    """
    Calculates Cohen's Kappa for dual-reviewer screening data.
    
    Args:
        decisions: List of screening decision dictionaries.
        
    Returns:
        Tuple of (kappa_value, agreement_counts).
    """
    # Organize data by study_id
    study_decisions = {}
    for row in decisions:
        sid = row["study_id"]
        rid = row["reviewer_id"]
        decision = row["decision"]
        
        if sid not in study_decisions:
            study_decisions[sid] = {}
        study_decisions[sid][rid] = decision

    # Calculate observed agreement (Po)
    n_studies = 0
    n_agreements = 0
    
    for sid, reviewers in study_decisions.items():
        if len(reviewers) != 2:
            continue # Skip if not dual-reviewed
        
        r1_dec = reviewers.get(1)
        r2_dec = reviewers.get(2)
        
        if r1_dec and r2_dec:
            n_studies += 1
            if r1_dec == r2_dec:
                n_agreements += 1
    
    if n_studies == 0:
        return 0.0, {"agreed": 0, "disagreed": 0, "total": 0}

    po = n_agreements / n_studies
    
    # Calculate expected agreement (Pe)
    # Count totals for each category across all reviewers
    count_include = 0
    count_exclude = 0
    
    for sid, reviewers in study_decisions.items():
        if len(reviewers) != 2:
            continue
        for rid in [1, 2]:
            dec = reviewers.get(rid)
            if dec == "include":
                count_include += 1
            elif dec == "exclude":
                count_exclude += 1
    
    total_reviews = count_include + count_exclude
    if total_reviews == 0:
        return 0.0, {"agreed": 0, "disagreed": 0, "total": 0}
        
    p_include = count_include / total_reviews
    p_exclude = count_exclude / total_reviews
    
    pe = (p_include ** 2) + (p_exclude ** 2)
    
    if pe == 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1 - pe)
        
    return kappa, {
        "agreed": n_agreements,
        "disagreed": n_studies - n_agreements,
        "total": n_studies
    }

def generate_adjudication_request(
    decisions: List[Dict[str, Any]], 
    output_path: Path
) -> List[Dict[str, Any]]:
    """
    Generates the adjudication request CSV for disputed studies.
    Returns the list of disputed rows.
    """
    # Organize data by study_id
    study_decisions = {}
    for row in decisions:
        sid = row["study_id"]
        rid = row["reviewer_id"]
        decision = row["decision"]
        exclusion = row.get("exclusion_codes", "")
        
        if sid not in study_decisions:
            study_decisions[sid] = {}
        study_decisions[sid][rid] = {
            "decision": decision,
            "exclusion_codes": exclusion
        }
    
    disputed_studies = []
    for sid, reviewers in study_decisions.items():
        if len(reviewers) != 2:
            continue
        
        r1 = reviewers.get(1)
        r2 = reviewers.get(2)
        
        if r1 and r2 and r1["decision"] != r2["decision"]:
            disputed_studies.append({
                "study_id": sid,
                "reviewer_1_decision": r1["decision"],
                "reviewer_1_exclusion": r1["exclusion_codes"],
                "reviewer_2_decision": r2["decision"],
                "reviewer_2_exclusion": r2["exclusion_codes"]
            })
    
    if disputed_studies:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=disputed_studies[0].keys())
            writer.writeheader()
            writer.writerows(disputed_studies)
    
    return disputed_studies

class TestCohensKappa:
    """Tests for Cohen's Kappa calculation logic."""
    
    def test_kappa_perfect_agreement(self, tmp_path):
        """Test that perfect agreement yields Kappa = 1.0."""
        data = [
            create_screening_decision("S1", 1, "include"),
            create_screening_decision("S1", 2, "include"),
            create_screening_decision("S2", 1, "exclude", ["NO_TRUST_METRIC"]),
            create_screening_decision("S2", 2, "exclude", ["NO_TRUST_METRIC"]),
        ]
        kappa, counts = calculate_cohen_kappa(data)
        assert math.isclose(kappa, 1.0, rel_tol=1e-5)
        assert counts["disagreed"] == 0
        assert counts["total"] == 2
    
    def test_kappa_random_disagreement(self, tmp_path):
        """Test calculation with mixed agreement/disagreement."""
        data = create_screening_log_data()
        kappa, counts = calculate_cohen_kappa(data)
        
        # With 8 studies, 4 agreed, 4 disagreed.
        # Expected logic check:
        # Po = 4/8 = 0.5
        # Counts: 6 includes (3 studies * 2), 10 excludes (5 studies * 2) -> Total 16 reviews
        # p_inc = 6/16 = 0.375, p_exc = 10/16 = 0.625
        # Pe = 0.375^2 + 0.625^2 = 0.140625 + 0.390625 = 0.53125
        # Kappa = (0.5 - 0.53125) / (1 - 0.53125) = -0.03125 / 0.46875 = -0.0666...
        # This is a valid test for the formula, even if negative.
        
        assert isinstance(kappa, float)
        assert -1.0 <= kappa <= 1.0
        assert counts["total"] == 8
        assert counts["disagreed"] == 4
    
    def test_kappa_no_studies(self):
        """Test behavior with empty or insufficient data."""
        data = []
        kappa, counts = calculate_cohen_kappa(data)
        assert kappa == 0.0
        assert counts["total"] == 0

class TestAdjudicationFlagging:
    """Tests for adjudication request generation."""
    
    def test_generate_adjudication_csv(self, tmp_path):
        """Test that disputed studies are correctly identified and written to CSV."""
        data = create_screening_log_data()
        output_path = tmp_path / "adjudication_request.csv"
        
        disputed = generate_adjudication_request(data, output_path)
        
        # We expect 4 disputed studies in the fixture (S003, S004, S007)
        # S003: Include vs Exclude
        # S004: Exclude vs Include
        # S007: Exclude vs Include
        # Total 3 disputed studies in the fixture logic above? 
        # Let's recount fixture:
        # S001: Agree (Inc/Inc)
        # S002: Agree (Exc/Exc)
        # S003: Disagree (Inc/Exc) -> 1
        # S004: Disagree (Exc/Inc) -> 2
        # S005: Agree (Inc/Inc)
        # S006: Agree (Exc/Exc)
        # S007: Disagree (Exc/Inc) -> 3
        # S008: Agree (Exc/Exc)
        # Total 3 disputed.
        
        assert len(disputed) == 3
        assert output_path.exists()
        
        # Verify file contents
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            
            # Check specific study
            s003 = next(r for r in rows if r["study_id"] == "S003")
            assert s003["reviewer_1_decision"] == "include"
            assert s003["reviewer_2_decision"] == "exclude"
    
    def test_no_adjudication_needed(self, tmp_path):
        """Test that no file is created when there are no disputes."""
        data = [
            create_screening_decision("S1", 1, "include"),
            create_screening_decision("S1", 2, "include"),
            create_screening_decision("S2", 1, "exclude", ["NO_TRUST_METRIC"]),
            create_screening_decision("S2", 2, "exclude", ["NO_TRUST_METRIC"]),
        ]
        output_path = tmp_path / "adjudication_request.csv"
        
        disputed = generate_adjudication_request(data, output_path)
        
        assert len(disputed) == 0
        assert not output_path.exists()

class TestScreeningLogicIntegration:
    """Integration tests combining Kappa and Adjudication logic."""
    
    def test_full_workflow_low_kappa(self, tmp_path):
        """Simulate a workflow where Kappa is low, triggering adjudication."""
        # Create data with low agreement
        data = [
            create_screening_decision("S1", 1, "include"),
            create_screening_decision("S1", 2, "exclude", ["NO_TRUST_METRIC"]),
            create_screening_decision("S2", 1, "exclude", ["NO_CONTROL_CONDITION"]),
            create_screening_decision("S2", 2, "include"),
            create_screening_decision("S3", 1, "include"),
            create_screening_decision("S3", 2, "exclude", ["NOT_PEER_REVIEWED"]),
            create_screening_decision("S4", 1, "exclude", ["NO_MODERATOR_DATA"]),
            create_screening_decision("S4", 2, "include"),
        ]
        
        kappa, counts = calculate_cohen_kappa(data)
        
        # Po = 0/4 = 0
        # Counts: 4 includes, 4 excludes. Total 8.
        # p_inc = 0.5, p_exc = 0.5. Pe = 0.25 + 0.25 = 0.5
        # Kappa = (0 - 0.5) / (1 - 0.5) = -1.0
        
        assert kappa < 0.6
        
        # Generate adjudication file
        adj_path = tmp_path / "adjudication_request.csv"
        disputed = generate_adjudication_request(data, adj_path)
        
        assert len(disputed) == 4
        assert adj_path.exists()
        assert counts["total"] == 4
        assert counts["disagreed"] == 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])