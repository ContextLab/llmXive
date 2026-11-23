import pytest
import os
import csv
import json
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from corrected_p_values_saver import (
    load_raw_p_values,
    load_bh_correction_factors,
    apply_bh_correction_to_raw,
    save_corrected_p_values,
    run_corrected_p_values_generation
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def raw_p_values_csv(temp_dir):
    """Create a sample raw p-values CSV file."""
    csv_path = Path(temp_dir) / "raw_p_values.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'raw_p'])
        writer.writeheader()
        writer.writerow({'query_id': 'Q1', 'metric': 'ndcg_at_k', 'raw_p': '0.02'})
        writer.writerow({'query_id': 'Q1', 'metric': 'map_at_k', 'raw_p': '0.05'})
        writer.writerow({'query_id': 'Q2', 'metric': 'ndcg_at_k', 'raw_p': '0.10'})
    return csv_path

@pytest.fixture
def bh_factors_json(temp_dir):
    """Create a sample BH correction factors JSON file."""
    json_path = Path(temp_dir) / "bh_factors.json"
    data = {
        'ndcg_at_k': {'Q1': 2.0, 'Q2': 1.5},
        'map_at_k': {'Q1': 1.0}
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return json_path

def test_load_raw_p_values(temp_dir, raw_p_values_csv):
    """Test loading raw p-values from CSV."""
    data = load_raw_p_values(raw_p_values_csv)
    assert len(data) == 3
    assert data[0]['query_id'] == 'Q1'
    assert data[0]['metric'] == 'ndcg_at_k'
    assert data[0]['raw_p'] == 0.02

def test_load_bh_correction_factors(temp_dir, bh_factors_json):
    """Test loading BH correction factors from JSON."""
    factors = load_bh_correction_factors(bh_factors_json)
    assert 'ndcg_at_k' in factors
    assert factors['ndcg_at_k']['Q1'] == 2.0

def test_apply_bh_correction_to_raw(temp_dir, raw_p_values_csv, bh_factors_json):
    """Test applying BH correction to raw p-values."""
    raw_p_values = load_raw_p_values(raw_p_values_csv)
    bh_factors = load_bh_correction_factors(bh_factors_json)
    
    corrected_data = apply_bh_correction_to_raw(raw_p_values, bh_factors)
    
    assert len(corrected_data) == 3
    
    # Check Q1 ndcg_at_k: raw_p=0.02, factor=2.0 -> corrected_p=0.04
    q1_ndcg = next(item for item in corrected_data if item['query_id'] == 'Q1' and item['metric'] == 'ndcg_at_k')
    assert abs(q1_ndcg['corrected_p'] - 0.04) < 1e-6
    assert q1_ndcg['is_significant'] == True  # 0.04 <= 0.05

    # Check Q2 ndcg_at_k: raw_p=0.10, factor=1.5 -> corrected_p=0.15
    q2_ndcg = next(item for item in corrected_data if item['query_id'] == 'Q2' and item['metric'] == 'ndcg_at_k')
    assert abs(q2_ndcg['corrected_p'] - 0.15) < 1e-6
    assert q2_ndcg['is_significant'] == False  # 0.15 > 0.05

def test_save_corrected_p_values(temp_dir, raw_p_values_csv, bh_factors_json):
    """Test saving corrected p-values to CSV."""
    raw_p_values = load_raw_p_values(raw_p_values_csv)
    bh_factors = load_bh_correction_factors(bh_factors_json)
    corrected_data = apply_bh_correction_to_raw(raw_p_values, bh_factors)
    
    output_path = Path(temp_dir) / "corrected_p_values.csv"
    save_corrected_p_values(corrected_data, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert 'query_id' in rows[0]
    assert 'metric' in rows[0]
    assert 'raw_p' in rows[0]
    assert 'corrected_p' in rows[0]
    assert 'is_significant' in rows[0]

def test_run_corrected_p_values_generation(temp_dir, raw_p_values_csv, bh_factors_json):
    """Test the full pipeline for generating corrected p-values."""
    output_path = Path(temp_dir) / "corrected_p_values.csv"
    
    # Mock the config to use temp_dir
    import corrected_p_values_saver
    original_results_dir = corrected_p_values_saver.RESULTS_DIR
    corrected_p_values_saver.RESULTS_DIR = Path(temp_dir)
    
    try:
        run_corrected_p_values_generation(
            raw_p_values_path=raw_p_values_csv,
            bh_factors_path=bh_factors_json,
            output_path=output_path
        )
        assert output_path.exists()
    finally:
        corrected_p_values_saver.RESULTS_DIR = original_results_dir
