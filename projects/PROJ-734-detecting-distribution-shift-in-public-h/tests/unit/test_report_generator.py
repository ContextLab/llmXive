"""
Unit tests for the report generator module.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from report_generator import load_metrics, load_flags, load_ground_truth
from report_generator import create_summary_plot, create_timeline_plot
from report_generator import generate_report

@pytest.fixture
def temp_metrics_file():
    """Create a temporary metrics CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("precision,recall,f1_score,detection_delay_mean,detection_delay_std,total_flags,true_positives,false_positives,false_negatives,total_ground_truth_events\n")
        f.write("0.85,0.92,0.88,1.5,0.8,12,10,2,1,11\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_flags_file():
    """Create a temporary flags CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("week,mmd_statistic,p_value\n")
        f.write("2019-W01,0.125,0.001\n")
        f.write("2019-W05,0.142,0.002\n")
        f.write("2019-W12,0.118,0.003\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_gt_file():
    """Create a temporary ground truth CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("start_week,end_week,event_name\n")
        f.write("2019-W02,2019-W04,Flu Outbreak A\n")
        f.write("2019-W10,2019-W12,Flu Outbreak B\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_metrics(temp_metrics_file):
    """Test loading metrics from CSV."""
    metrics = load_metrics(temp_metrics_file)
    assert metrics['precision'] == 0.85
    assert metrics['recall'] == 0.92
    assert metrics['f1_score'] == 0.88
    assert metrics['detection_delay_mean'] == 1.5
    assert metrics['total_flags'] == 12

def test_load_flags(temp_flags_file):
    """Test loading flags from CSV."""
    flags = load_flags(temp_flags_file)
    assert len(flags) == 3
    assert 'week' in flags.columns
    assert 'mmd_statistic' in flags.columns
    assert flags.iloc[0]['week'] == '2019-W01'

def test_load_ground_truth(temp_gt_file):
    """Test loading ground truth from CSV."""
    gt = load_ground_truth(temp_gt_file)
    assert len(gt) == 2
    assert 'start_week' in gt.columns
    assert 'event_name' in gt.columns
    assert gt.iloc[0]['event_name'] == 'Flu Outbreak A'

def test_load_metrics_missing_file():
    """Test error handling for missing metrics file."""
    with pytest.raises(FileNotFoundError):
        load_metrics('nonexistent_file.csv')

def test_load_flags_missing_file():
    """Test error handling for missing flags file."""
    with pytest.raises(FileNotFoundError):
        load_flags('nonexistent_file.csv')

def test_load_ground_truth_missing_file():
    """Test error handling for missing ground truth file."""
    with pytest.raises(FileNotFoundError):
        load_ground_truth('nonexistent_file.csv')

def test_create_summary_plot(temp_metrics_file, tmp_path):
    """Test summary plot generation."""
    metrics = load_metrics(temp_metrics_file)
    output_path = str(tmp_path / 'summary.png')
    create_summary_plot(metrics, output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_create_timeline_plot(temp_flags_file, temp_gt_file, tmp_path):
    """Test timeline plot generation."""
    flags = load_flags(temp_flags_file)
    gt = load_ground_truth(temp_gt_file)
    output_path = str(tmp_path / 'timeline.png')
    create_timeline_plot(flags, gt, output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_generate_report(temp_metrics_file, temp_flags_file, temp_gt_file, tmp_path):
    """Test full report generation."""
    output_pdf = str(tmp_path / 'report.pdf')
    generate_report(temp_metrics_file, temp_flags_file, temp_gt_file, output_pdf)
    assert os.path.exists(output_pdf)
    assert os.path.getsize(output_pdf) > 0
    # Basic check for PDF magic bytes
    with open(output_pdf, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF'
