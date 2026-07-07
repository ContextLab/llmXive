import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.data.preprocess import generate_data_quality_report

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        raw_dir = data_dir / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create a mock interactions file with known missing values
        data = {
            'pathogen_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P3'],
            'host_id': ['H1', 'H2', 'H3', 'H1', 'H2', 'H1'],
            'interaction': [1, 0, 'unknown', 1, 'unknown', 1]
        }
        df = pd.DataFrame(data)
        csv_path = raw_dir / "interactions_merged.csv"
        df.to_csv(csv_path, index=False)
        
        yield str(data_dir)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp

def test_generate_data_quality_report_creates_file(temp_data_dir, temp_output_dir):
    result = generate_data_quality_report(temp_data_dir, temp_output_dir)
    
    report_path = Path(temp_output_dir) / "reports" / "data_quality_report.json"
    assert report_path.exists(), "Report file should be created"
    assert isinstance(result, dict), "Function should return a dict"

def test_generate_data_quality_report_content(temp_data_dir, temp_output_dir):
    generate_data_quality_report(temp_data_dir, temp_output_dir)
    
    report_path = Path(temp_output_dir) / "reports" / "data_quality_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert 'summary' in report
    assert 'per_pathogen_details' in report
    
    # Check specific values based on the fixture data:
    # P1: 3 total, 1 missing (unknown) -> 33.33%
    # P2: 2 total, 1 missing (unknown) -> 50.00%
    # P3: 1 total, 0 missing -> 0.00%
    
    p2_data = next(p for p in report['per_pathogen_details'] if p['pathogen_id'] == 'P2')
    assert p2_data['missing_percentage'] == 50.0, "P2 should have 50% missing"
    assert p2_data['missing_interactions_count'] == 1
    
    assert report['summary']['overall_missing_percentage'] > 0

def test_generate_data_quality_report_no_missing(temp_data_dir, temp_output_dir):
    # Modify the temp file to have no missing values
    raw_path = Path(temp_data_dir) / "raw" / "interactions_merged.csv"
    df = pd.read_csv(raw_path)
    df['interaction'] = df['interaction'].replace('unknown', 1)
    df.to_csv(raw_path, index=False)
    
    generate_data_quality_report(temp_data_dir, temp_output_dir)
    
    report_path = Path(temp_output_dir) / "reports" / "data_quality_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['summary']['overall_missing_percentage'] == 0.0

def test_generate_data_quality_report_empty_input(temp_data_dir, temp_output_dir):
    # Create an empty file
    raw_path = Path(temp_data_dir) / "raw" / "interactions_merged.csv"
    pd.DataFrame(columns=['pathogen_id', 'host_id', 'interaction']).to_csv(raw_path, index=False)
    
    result = generate_data_quality_report(temp_data_dir, temp_output_dir)
    
    report_path = Path(temp_output_dir) / "reports" / "data_quality_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['summary']['total_records_analyzed'] == 0
    assert report['summary']['overall_missing_percentage'] == 0.0
