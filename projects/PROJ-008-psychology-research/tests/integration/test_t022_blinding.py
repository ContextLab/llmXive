import pytest
import json
import tempfile
from pathlib import Path
from code.data.cleaner import clean_studies, filter_included_studies
from code.data.extractor import extract_blinding_status

def test_t022_blinding_extraction_integration():
    """Integration test for T022: Blinded Assessment Logic."""
    # Use mock data from T015c
    mock_data = [
        {
            "id": "study-A",
            "title": "Study A",
            "registry": "ClinicalTrials.gov",
            "age_range": {"min": 8, "max": 10},
            "diagnosis": "ASD",
            "outcomes": ["Social skill improvement"],
            "intervention_components": ["breathing"],
            "delivery_format": "caregiver-mediated",
            "social_skill_domain": "communication",
            "rater_type": "unblinded",
            "blinded_assessment_flag": False
        },
        {
            "id": "study-B",
            "title": "Study B",
            "registry": "OSF",
            "age_range": {"min": 8, "max": 12},
            "diagnosis": "ASD",
            "outcomes": ["Social skill improvement"],
            "intervention_components": ["body scan"],
            "delivery_format": "child-led",
            "social_skill_domain": "peer interaction",
            "rater_type": "blinded",
            "blinded_assessment_flag": True
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_csv = tmpdir_path / "cleaned_studies.csv"
        excluded_log = tmpdir_path / "excluded_studies.log"

        # Run cleaning process
        clean_studies(mock_data, output_csv, excluded_log)

        # Verify output CSV exists and contains blinding columns
        assert output_csv.exists()
        import pandas as pd
        df = pd.read_csv(output_csv)

        assert "rater_type" in df.columns
        assert "blinded_assessment_flag" in df.columns

        # Verify values
        study_a = df[df["id"] == "study-A"].iloc[0]
        study_b = df[df["id"] == "study-B"].iloc[0]

        assert study_a["rater_type"] == "unblinded"
        assert study_a["blinded_assessment_flag"] == False
        assert study_b["rater_type"] == "blinded"
        assert study_b["blinded_assessment_flag"] == True
