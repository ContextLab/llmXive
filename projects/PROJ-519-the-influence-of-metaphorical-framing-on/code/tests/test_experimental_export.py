"""
Tests for T016: Experimental Export Logic.

Verifies that:
1. The export function correctly merges assignments and survey responses.
2. The output CSV is written to the correct path.
3. The SHA-256 checksum file is generated and matches the CSV content.
4. Missing input files raise FileNotFoundError.
"""
import os
import csv
import json
import tempfile
import hashlib
import pytest
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from experimental_export import export_experimental_results, compute_sha256

def test_export_creates_csv_and_checksum():
    """Test that export creates the CSV and its checksum file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare inputs
        assignments_path = os.path.join(tmpdir, "assignments.csv")
        responses_path = os.path.join(tmpdir, "responses.json")
        output_csv = os.path.join(tmpdir, "results.csv")
        output_checksum = os.path.join(tmpdir, "results.csv.sha256")

        # Create dummy assignments
        assignments_data = [
            {"participant_id": "P001", "condition": "Battle", "vignette_text": "Battle text...", "timestamp": "2023-01-01T00:00:00"},
            {"participant_id": "P002", "condition": "Journey", "vignette_text": "Journey text...", "timestamp": "2023-01-01T00:01:00"}
        ]
        with open(assignments_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=assignments_data[0].keys())
            writer.writeheader()
            writer.writerows(assignments_data)

        # Create dummy survey responses
        # Structure must match what load_survey_responses expects
        responses_data = [
            {
                "participant_id": "P001",
                "responses": {
                    "q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5,
                    "q6": 6, "q7": 7, "q8": 8, "q9": 9, "q10": 10,
                    "q11": 11, "q12": 12, "q13": 13, "q14": 14,
                    "q15": 15, "q16": 16, "q17": 17, "q18": 18,
                    "q19": 19, "q20": 20, "q21": 21, "q22": 22,
                    "q23": 23, "q24": 24, "q25": 25, "q26": 26,
                    "q27": 27, "q28": 28, "q29": 29, "q30": 30,
                    "q31": 31, "q32": 32, "q33": 33, "q34": 34,
                    "q35": 35, "q36": 36, "q37": 37, "q38": 38,
                    "q39": 39, "q40": 40, "q41": 41, "q42": 42,
                    "q43": 43, "q44": 44, "q45": 45, "q46": 46,
                    "q47": 47, "q48": 48, "q49": 49, "q50": 50,
                    "q51": 51, "q52": 52, "q53": 53, "q54": 54,
                    "q55": 55, "q56": 56, "q57": 57, "q58": 58,
                    "q59": 59, "q60": 60, "q61": 61, "q62": 62,
                    "q63": 63, "q64": 64, "q65": 65, "q66": 66,
                    "q67": 67, "q68": 68, "q69": 69, "q70": 70,
                    "q71": 71, "q72": 72, "q73": 73, "q74": 74,
                    "q75": 75, "q76": 76, "q77": 77, "q78": 78,
                    "q79": 79, "q80": 80, "q81": 81, "q82": 82,
                    "q83": 83, "q84": 84, "q85": 85, "q86": 86,
                    "q87": 87, "q88": 88, "q89": 89, "q90": 90,
                    "q91": 91, "q92": 92, "q93": 93, "q94": 94,
                    "q95": 95, "q96": 96, "q97": 97, "q98": 98,
                    "q99": 99, "q100": 100,
                    "help_seeking": 5,
                    "attention_check": "Yes"
                }
            },
            {
                "participant_id": "P002",
                "responses": {
                    "q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5,
                    "q6": 6, "q7": 7, "q8": 8, "q9": 9, "q10": 10,
                    "q11": 11, "q12": 12, "q13": 13, "q14": 14,
                    "q15": 15, "q16": 16, "q17": 17, "q18": 18,
                    "q19": 19, "q20": 20, "q21": 21, "q22": 22,
                    "q23": 23, "q24": 24, "q25": 25, "q26": 26,
                    "q27": 27, "q28": 28, "q29": 29, "q30": 30,
                    "q31": 31, "q32": 32, "q33": 33, "q34": 34,
                    "q35": 35, "q36": 36, "q37": 37, "q38": 38,
                    "q39": 39, "q40": 40, "q41": 41, "q42": 42,
                    "q43": 43, "q44": 44, "q45": 45, "q46": 46,
                    "q47": 47, "q48": 48, "q49": 49, "q50": 50,
                    "q51": 51, "q52": 52, "q53": 53, "q54": 54,
                    "q55": 55, "q56": 56, "q57": 57, "q58": 58,
                    "q59": 59, "q60": 60, "q61": 61, "q62": 62,
                    "q63": 63, "q64": 64, "q65": 65, "q66": 66,
                    "q67": 67, "q68": 68, "q69": 69, "q70": 70,
                    "q71": 71, "q72": 72, "q73": 73, "q74": 74,
                    "q75": 75, "q76": 76, "q77": 77, "q78": 78,
                    "q79": 79, "q80": 80, "q81": 81, "q82": 82,
                    "q83": 83, "q84": 84, "q85": 85, "q86": 86,
                    "q87": 87, "q88": 88, "q89": 89, "q90": 90,
                    "q91": 91, "q92": 92, "q93": 93, "q94": 94,
                    "q95": 95, "q96": 96, "q97": 97, "q98": 98,
                    "q99": 99, "q100": 100,
                    "help_seeking": 4,
                    "attention_check": "Yes"
                }
            }
        ]
        with open(responses_path, 'w') as f:
            json.dump(responses_data, f)

        # Run export
        export_experimental_results(
            assignments_path=assignments_path,
            survey_responses_path=responses_path,
            output_csv_path=output_csv,
            checksum_path=output_checksum
        )

        # Verify files exist
        assert os.path.exists(output_csv)
        assert os.path.exists(output_checksum)

        # Verify CSV content
        with open(output_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['participant_id'] == 'P001'
            assert rows[0]['condition'] == 'Battle'
            assert rows[1]['participant_id'] == 'P002'
            assert rows[1]['condition'] == 'Journey'

        # Verify checksum matches
        with open(output_checksum, 'r') as f:
            stored_checksum = f.read().split()[0]
        
        computed_checksum = compute_sha256(output_csv)
        assert stored_checksum == computed_checksum

def test_export_missing_assignments_raises():
    """Test that missing assignments file raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            export_experimental_results(
                assignments_path=os.path.join(tmpdir, "missing.csv"),
                survey_responses_path=os.path.join(tmpdir, "responses.json"),
                output_csv_path=os.path.join(tmpdir, "results.csv")
            )

def test_export_missing_responses_raises():
    """Test that missing responses file raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy assignments
        assignments_path = os.path.join(tmpdir, "assignments.csv")
        with open(assignments_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id', 'condition', 'vignette_text', 'timestamp'])
            writer.writeheader()
            writer.writerow({'participant_id': 'P001', 'condition': 'Battle', 'vignette_text': '...', 'timestamp': '...'})

        with pytest.raises(FileNotFoundError):
            export_experimental_results(
                assignments_path=assignments_path,
                survey_responses_path=os.path.join(tmpdir, "missing.json"),
                output_csv_path=os.path.join(tmpdir, "results.csv")
            )