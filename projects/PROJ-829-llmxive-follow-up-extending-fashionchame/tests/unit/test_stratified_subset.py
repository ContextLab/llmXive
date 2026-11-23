import pytest
import json
import tempfile
from pathlib import Path
from src.data.stratified_subset import (
    load_filtered_manifest,
    stratify_samples,
    validate_subset_balance,
    save_stratified_subset,
    run_pipeline
)

@pytest.fixture
def sample_data():
    return [
        {"id": "1", "GarmentFeatureClass": "Color", "optical_flow_magnitude": 0.5},
        {"id": "2", "GarmentFeatureClass": "Color", "optical_flow_magnitude": 0.6},
        {"id": "3", "GarmentFeatureClass": "Pattern", "optical_flow_magnitude": 0.4},
        {"id": "4", "GarmentFeatureClass": "Texture", "optical_flow_magnitude": 0.7},
        {"id": "5", "GarmentFeatureClass": "Texture", "optical_flow_magnitude": 0.8},
    ]

def test_load_filtered_manifest(tmp_path, sample_data):
    input_file = tmp_path / "filtered.json"
    with open(input_file, 'w') as f:
        json.dump(sample_data, f)
    
    result = load_filtered_manifest(str(input_file))
    assert len(result) == 5
    assert result[0]["id"] == "1"

def test_stratify_samples(sample_data):
    stratified = stratify_samples(sample_data)
    assert "Color" in stratified
    assert "Pattern" in stratified
    assert "Texture" in stratified
    assert len(stratified["Color"]) == 2
    assert len(stratified["Pattern"]) == 1
    assert len(stratified["Texture"]) == 2

def test_validate_subset_balance_high():
    data = {"A": [1, 2, 3, 4, 5], "B": [1, 2, 3, 4, 5]}
    assert validate_subset_balance(data, min_count=3) is True

def test_validate_subset_balance_low():
    data = {"A": [1, 2], "B": [1, 2, 3, 4, 5]}
    assert validate_subset_balance(data, min_count=3) is False

def test_save_stratified_subset(tmp_path, sample_data):
    stratified = stratify_samples(sample_data)
    output_file = tmp_path / "stratified.json"
    
    save_stratified_subset(stratified, str(output_file))
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["stratified_by"] == "GarmentFeatureClass"
    assert "Color" in manifest["classes"]
    assert len(manifest["classes"]["Color"]["sample_ids"]) == 2
    # Verify full sample data is preserved
    assert len(manifest["classes"]["Color"]["samples"]) == 2
    assert manifest["classes"]["Color"]["samples"][0]["optical_flow_magnitude"] == 0.5

def test_run_pipeline(tmp_path, sample_data):
    input_file = tmp_path / "filtered.json"
    output_file = tmp_path / "stratified.json"
    
    with open(input_file, 'w') as f:
        json.dump(sample_data, f)
    
    run_pipeline(str(input_file), str(output_file))
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        manifest = json.load(f)
    
    assert "classes" in manifest
    assert manifest["total_samples"] == 5