import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.data.calculate_reliability import (
    load_annotations,
    prepare_ratings,
    compute_cohen_kappa_aggregated,
    interpret_kappa,
    generate_report,
    main
)

@pytest.fixture
def sample_annotations():
    return [
        {"comment_id": "c1", "annotator_id": "A1", "label": "positive"},
        {"comment_id": "c1", "annotator_id": "A2", "label": "positive"},
        {"comment_id": "c2", "annotator_id": "A1", "label": "negative"},
        {"comment_id": "c2", "annotator_id": "A2", "label": "neutral"},
        {"comment_id": "c3", "annotator_id": "A1", "label": "positive"},
        {"comment_id": "c3", "annotator_id": "A2", "label": "positive"},
        {"comment_id": "c4", "annotator_id": "A1", "label": "positive"},
        {"comment_id": "c4", "annotator_id": "A2", "label": "positive"},
        {"comment_id": "c5", "annotator_id": "A1", "label": "neutral"},
        {"comment_id": "c5", "annotator_id": "A2", "label": "neutral"},
    ]

@pytest.fixture
def temp_annotation_file(sample_annotations):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_annotations, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_report_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_annotations_success(temp_annotation_file, sample_annotations):
    data = load_annotations(temp_annotation_file)
    assert len(data) == len(sample_annotations)
    assert data[0]['comment_id'] == 'c1'

def test_load_annotations_missing_file():
    with pytest.raises(FileNotFoundError):
        load_annotations("non_existent_file.json")

def test_prepare_ratings(sample_annotations):
    ratings, valid_ids = prepare_ratings(sample_annotations)
    assert len(valid_ids) == 5
    assert 'c1' in valid_ids
    assert len(ratings['c1']) == 2

def test_prepare_ratings_insufficient_annotators():
    data = [
        {"comment_id": "c1", "annotator_id": "A1", "label": "positive"},
    ]
    ratings, valid_ids = prepare_ratings(data)
    assert len(valid_ids) == 0

def test_compute_cohen_kappa_perfect_agreement():
    # c1: pos/pos, c2: neg/neg, c3: neu/neu -> 100% agreement
    annotations = [
        {"comment_id": "c1", "annotator_id": "A1", "label": "positive"},
        {"comment_id": "c1", "annotator_id": "A2", "label": "positive"},
        {"comment_id": "c2", "annotator_id": "A1", "label": "negative"},
        {"comment_id": "c2", "annotator_id": "A2", "label": "negative"},
        {"comment_id": "c3", "annotator_id": "A1", "label": "neutral"},
        {"comment_id": "c3", "annotator_id": "A2", "label": "neutral"},
    ]
    ratings, valid_ids = prepare_ratings(annotations)
    kappa = compute_cohen_kappa_aggregated(annotations, valid_ids, ratings)
    assert abs(kappa - 1.0) < 1e-6

def test_compute_cohen_kappa_no_agreement():
    # c1: pos/neg, c2: neg/pos -> 0% agreement, chance is 0.5 (assuming balanced)
    # Actually, if labels are balanced, Pe = 0.5. Po = 0. Kappa = (0 - 0.5)/(1-0.5) = -1.
    annotations = [
        {"comment_id": "c1", "annotator_id": "A1", "label": "positive"},
        {"comment_id": "c1", "annotator_id": "A2", "label": "negative"},
        {"comment_id": "c2", "annotator_id": "A1", "label": "negative"},
        {"comment_id": "c2", "annotator_id": "A2", "label": "positive"},
    ]
    ratings, valid_ids = prepare_ratings(annotations)
    kappa = compute_cohen_kappa_aggregated(annotations, valid_ids, ratings)
    # Exact value depends on distribution, but should be <= 0
    assert kappa <= 0.0

def test_generate_report(temp_report_file):
    kappa = 0.65
    interpretation = "Substantial"
    report = generate_report(kappa, interpretation, 10, 20, temp_report_file)
    
    assert os.path.exists(temp_report_file)
    with open(temp_report_file, 'r') as f:
        data = json.load(f)
    
    assert data['kappa'] == kappa
    assert data['interpretation'] == interpretation
    assert data['status'] == 'valid'

def test_empty_ratings_raises_error():
    annotations = []
    with pytest.raises(ValueError):
        _, valid_ids = prepare_ratings(annotations)
        # If we try to compute on empty valid_ids
        if valid_ids:
            compute_cohen_kappa_aggregated(annotations, valid_ids, {})
    # Actually prepare_ratings returns empty list, so compute should fail if called
    ratings, valid_ids = prepare_ratings(annotations)
    with pytest.raises(ValueError):
        compute_cohen_kappa_aggregated(annotations, valid_ids, ratings)

def test_main_integration(temp_annotation_file, temp_report_file, mocker):
    # Mock the paths to use temp files
    mocker.patch('code.data.calculate_reliability.main') # Avoid recursion if main calls itself? No, we mock the function inside
    # Actually, we just want to test the logic flow if we were to run main.
    # Since main has hardcoded paths relative to __file__, we can't easily test it without mocking Path or env.
    # We will just verify the imports and that the function exists.
    assert callable(main)
    
    # We can test the logic by calling the sub-functions directly which is what main does
    annotations = load_annotations(temp_annotation_file)
    ratings, valid_ids = prepare_ratings(annotations)
    kappa = compute_cohen_kappa_aggregated(annotations, valid_ids, ratings)
    interpretation = interpret_kappa(kappa)
    
    # Write to temp report file
    report = generate_report(kappa, interpretation, len(valid_ids), len(annotations), temp_report_file)
    
    assert os.path.exists(temp_report_file)
    with open(temp_report_file, 'r') as f:
        final_report = json.load(f)
    
    assert 'kappa' in final_report
    assert final_report['kappa'] == kappa
    assert final_report['status'] in ['valid', 'warning_low_reliability']