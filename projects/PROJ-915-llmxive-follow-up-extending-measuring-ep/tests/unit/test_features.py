import pytest
import csv
import os
import sys
from pathlib import Path
import tempfile

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import (
    count_sentences,
    count_modal_verbs,
    count_imperative_sentences,
    count_declarative_sentences,
    count_citations,
    extract_features,
    flag_undefined_imperative_ratio,
    run_feature_extraction_pipeline
)

class TestSentenceCounting:
    def test_count_sentences_simple(self):
        text = "Hello world. This is a test."
        assert count_sentences(text) == 2

    def test_count_sentences_empty(self):
        assert count_sentences("") == 0
        assert count_sentences(None) == 0

    def test_count_sentences_no_ending(self):
        text = "Hello world"
        assert count_sentences(text) == 1

    def test_count_sentences_multiple_ending(self):
        text = "Wait! Stop! Go!"
        assert count_sentences(text) == 3

class TestModalVerbs:
    def test_count_modal_verbs_present(self):
        text = "You must do this. Can you help? I will try."
        assert count_modal_verbs(text) == 3

    def test_count_modal_verbs_empty(self):
        assert count_modal_verbs("") == 0

    def test_count_modal_verbs_case_insensitive(self):
        text = "MUST you go? MAY I stay?"
        assert count_modal_verbs(text) == 2

class TestImperativeDeclarative:
    def test_count_imperative_sentences(self):
        text = "Please do this. Do not touch. Try again."
        assert count_imperative_sentences(text) == 3

    def test_count_declarative_sentences(self):
        text = "The sky is blue. It is raining."
        # Assuming these are not flagged as imperative
        assert count_declarative_sentences(text) == 2

    def test_count_declarative_mixed(self):
        text = "Please sit down. The chair is broken."
        # 1 imperative, 2 total sentences -> 1 declarative
        assert count_declarative_sentences(text) == 1

class TestCitations:
    def test_count_citations_brackets(self):
        text = "Studies show [1] and [2, 3] that this is true."
        assert count_citations(text) == 2

    def test_count_citations_parentheses(self):
        text = "As Smith (2020) noted, this is the case."
        assert count_citations(text) == 1

    def test_count_citations_mixed(self):
        text = "See [1] (Doe, 2019)."
        assert count_citations(text) == 2

class TestExtractFeatures:
    def test_extract_features_normal(self):
        text = "Please answer this question. It is important. [1]"
        features = extract_features(text)
        assert features['num_sentences'] == 2
        assert features['num_imperative'] == 1
        assert features['num_citations'] == 1
        assert features['modal_freq'] == 0.0
        assert features['citation_density'] == 0.5

    def test_extract_features_empty(self):
        features = extract_features("")
        assert features['num_sentences'] == 0
        assert features['modal_freq'] == 0.0
        assert features['imperative_ratio'] is None
        assert features['citation_density'] == 0.0

class TestUndefinedRatioHandling:
    def test_flag_undefined_ratio_zero_sentences(self):
        row = {'num_sentences': 0, 'imperative_ratio': None}
        is_undef, safe_val = flag_undefined_imperative_ratio(row)
        assert is_undef is True
        assert safe_val == 0.0

    def test_flag_defined_ratio(self):
        row = {'num_sentences': 5, 'imperative_ratio': 0.4}
        is_undef, safe_val = flag_undefined_imperative_ratio(row)
        assert is_undef is False
        assert safe_val == 0.4

    def test_flag_zero_sentences_imperative_zero(self):
        row = {'num_sentences': 0, 'imperative_ratio': 0.0}
        is_undef, safe_val = flag_undefined_imperative_ratio(row)
        assert is_undef is True
        assert safe_val == 0.0

class TestIntegrationPipeline:
    def test_run_feature_extraction_pipeline_creates_file(self):
        # Create a temporary CSV input
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Mock input data
            with open(input_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['prompt_id', 'text'])
                writer.writeheader()
                writer.writerow({'prompt_id': '1', 'text': 'Please do this. [1]'})
                writer.writerow({'prompt_id': '2', 'text': ''}) # Zero sentences case
                writer.writerow({'prompt_id': '3', 'text': 'Normal sentence.'})

            # Temporarily override paths in the module
            import features
            original_raw = features.RAW_DATA_PATH
            original_proc = features.PROCESSED_DATA_PATH
            
            features.RAW_DATA_PATH = input_path
            features.PROCESSED_DATA_PATH = output_path
            
            try:
                run_feature_extraction_pipeline()
                
                # Verify output exists
                assert output_path.exists()
                
                # Verify content
                with open(output_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    assert len(rows) == 3
                    
                    # Check row 1 (normal)
                    r1 = rows[0]
                    assert r1['prompt_id'] == '1'
                    assert r1['is_ratio_undefined'] == 'False'
                    
                    # Check row 2 (empty/zero sentences)
                    r2 = rows[1]
                    assert r2['prompt_id'] == '2'
                    assert r2['is_ratio_undefined'] == 'True'
                    assert r2['ratio_safe_value'] == '0.0'
                    
                    # Check row 3 (normal)
                    r3 = rows[2]
                    assert r3['prompt_id'] == '3'
                    assert r3['is_ratio_undefined'] == 'False'
                    
            finally:
                features.RAW_DATA_PATH = original_raw
                features.PROCESSED_DATA_PATH = original_proc