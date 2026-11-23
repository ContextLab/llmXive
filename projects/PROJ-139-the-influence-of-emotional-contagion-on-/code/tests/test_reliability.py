"""
Tests for the calculate_reliability module (T007b).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.data.calculate_reliability import (
    load_annotations,
    prepare_ratings,
    compute_cohen_kappa,
    interpret_kappa,
    generate_report,
    main
)

@pytest.fixture
def sample_annotations():
    """Sample annotations data simulating T007a output."""
    return [
        {"comment_id": "c1", "text": "Great post", "annotator_1": "positive", "annotator_2": "positive"},
        {"comment_id": "c2", "text": "Bad info", "annotator_1": "negative", "annotator_2": "negative"},
        {"comment_id": "c3", "text": "Okay", "annotator_1": "neutral", "annotator_2": "positive"}, # Disagreement
        {"comment_id": "c4", "text": "Love it", "annotator_1": "positive", "annotator_2": "positive"},
    ]

@pytest.fixture
def temp_annotation_file(sample_annotations):
    """Creates a temporary file with sample annotations."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_annotations, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_load_annotations_success(temp_annotation_file):
    data = load_annotations(temp_annotation_file)
    assert len(data) == 4
    assert data[0]['comment_id'] == 'c1'

def test_load_annotations_missing_file():
    with pytest.raises(FileNotFoundError):
        load_annotations(Path("/nonexistent/path.json"))

def test_prepare_ratings(sample_annotations):
    r1, r2 = prepare_ratings(sample_annotations)
    assert len(r1) == 4
    assert r1['c1'] == 'positive'
    assert r2['c3'] == 'positive'
    assert r1['c3'] == 'neutral'

def test_prepare_ratings_insufficient_annotators():
    # Data with only one annotator column
    data = [{"comment_id": "c1", "annotator_1": "positive"}]
    with pytest.raises(ValueError, match="Need at least two annotators"):
        prepare_ratings(data)

def test_compute_cohen_kappa_perfect_agreement():
    r1 = {"c1": "pos", "c2": "neg"}
    r2 = {"c1": "pos", "c2": "neg"}
    kappa = compute_cohen_kappa(r1, r2)
    assert kappa == 1.0

def test_compute_cohen_kappa_no_agreement():
    # Construct a case with 0 observed agreement but high chance agreement to get negative kappa
    # Or simple case where they always disagree but categories are balanced
    r1 = {"c1": "A", "c2": "B"}
    r2 = {"c1": "B", "c2": "A"}
    # Po = 0/2 = 0
    # Freq1: A:1, B:1 -> pA=0.5, pB=0.5
    # Freq2: A:1, B:1 -> pA=0.5, pB=0.5
    # Pe = 0.5*0.5 + 0.5*0.5 = 0.5
    # Kappa = (0 - 0.5) / (1 - 0.5) = -1.0
    kappa = compute_cohen_kappa(r1, r2)
    assert kappa == -1.0

def test_generate_report(temp_annotation_file, tmp_path):
    data = load_annotations(temp_annotation_file)
    r1, r2 = prepare_ratings(data)
    kappa = compute_cohen_kappa(r1, r2)
    output_file = tmp_path / "report.json"
    
    report = generate_report(kappa, r1, r2, output_file)
    
    assert output_file.exists()
    assert "kappa" in report
    assert "interpretation" in report
    assert report["number_of_items"] == 4

def test_empty_ratings_raises_error(sample_annotations):
    # Modify to have no common keys effectively
    r1 = {"c1": "pos"}
    r2 = {"c2": "neg"}
    with pytest.raises(ValueError, match="No common items"):
        compute_cohen_kappa(r1, r2)

@patch('code.data.calculate_reliability.get_config')
@patch('code.data.calculate_reliability.load_annotations')
@patch('code.data.calculate_reliability.prepare_ratings')
@patch('code.data.calculate_reliability.compute_cohen_kappa')
@patch('code.data.calculate_reliability.generate_report')
def test_main_integration(mock_report, mock_kappa, mock_prepare, mock_load, mock_get_config, temp_annotation_file, tmp_path):
    # Mock config
    mock_config = MagicMock()
    mock_config.dataset_paths.raw_dir = temp_annotation_file.parent
    mock_config.dataset_paths.processed_dir = tmp_path
    mock_get_config.return_value = mock_config
    
    mock_load.return_value = [{"c": "1"}]
    mock_prepare.return_value = ({"c": "1"}, {"c": "1"})
    mock_kappa.return_value = 0.8
    mock_report.return_value = {"kappa": 0.8}
    
    main()
    
    mock_load.assert_called_once()
    mock_prepare.assert_called_once()
    mock_kappa.assert_called_once()
    mock_report.assert_called_once()
