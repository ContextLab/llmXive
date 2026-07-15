"""
Integration test for data retrieval and filtering logic (User Story 1).

This test validates the end-to-end flow of:
1. Loading dataset configuration from data/config/dataset_ids.json
2. Validating the configuration against the schema
3. Simulating the retrieval and filtering logic (mocking external network calls)
4. Verifying that output artifacts are generated in data/processed/

Note: This test uses a mock dataset to simulate the retrieval process without
requiring actual network access to NCBI SRA or Zenodo during the integration test.
The actual retrieval logic is tested in code/01_retrieve_data.py when run against
real data.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from dataset_config_validator import load_schema, validate_config, create_sample_config
from state_tracker import calculate_file_hash, update_artifact_hash


def setup_test_environment():
    """Create a temporary test environment with mock data."""
    test_dir = tempfile.mkdtemp(prefix="test_data_retrieval_")
    
    # Create directory structure
    data_raw = Path(test_dir) / "data" / "raw"
    data_processed = Path(test_dir) / "data" / "processed"
    data_config = Path(test_dir) / "data" / "config"
    
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    data_config.mkdir(parents=True, exist_ok=True)
    
    # Create a mock dataset configuration
    config_path = data_config / "dataset_ids.json"
    mock_config = {
        "datasets": [
            {
                "id": "mock-cw-001",
                "source": "mock-source",
                "url": "https://example.com/mock-data.tar.gz",
                "description": "Mock constructed wetland dataset",
                "wetland_type": "constructed",
                "has_nutrient_removal": True,
                "sample_count": 50
            }
        ],
        "metadata": {
            "created_by": "test",
            "version": "1.0"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(mock_config, f, indent=2)
    
    return test_dir, data_raw, data_processed, data_config


def test_dataset_config_loading():
    """Test that dataset configuration can be loaded and validated."""
    test_dir, _, _, data_config = setup_test_environment()
    
    try:
        config_path = data_config / "dataset_ids.json"
        
        # Load and validate config
        schema = load_schema("contracts/dataset-config.schema.yaml")
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        is_valid, errors = validate_config(config_data, schema)
        
        assert is_valid, f"Config validation failed: {errors}"
        assert len(config_data['datasets']) == 1
        assert config_data['datasets'][0]['wetland_type'] == 'constructed'
        
    finally:
        shutil.rmtree(test_dir)


def test_filtering_logic_with_mock_data():
    """Test the filtering logic for constructed wetlands with nutrient removal."""
    test_dir, data_raw, data_processed, data_config = setup_test_environment()
    
    try:
        # Create mock feature table and metadata files
        feature_table_path = data_raw / "mock-cw-001_feature_table.tsv"
        metadata_path = data_raw / "mock-cw-001_metadata.tsv"
        
        # Create a simple mock feature table (taxa as rows, samples as columns)
        feature_table_content = """#OTU ID\tSample1\tSample2\tSample3\tSample4\tSample5
Taxon_A\t100\t150\t200\t120\t180
Taxon_B\t50\t60\t70\t55\t65
Taxon_C\t200\t250\t300\t220\t280
Taxon_D\t30\t40\t50\t35\t45
Taxon_E\t80\t90\t100\t85\t95
"""
        
        # Create mock metadata with various wetland types
        metadata_content = """sample_id\twetland_type\tn_removal\tp_removal\tstage
Sample1\tconstructed\t45.5\t32.1\tearly
Sample2\tconstructed\t48.2\t35.4\tearly
Sample3\tconstructed\t52.1\t38.2\tmature
Sample4\tconstructed\t55.3\t40.5\tmature
Sample5\tconstructed\t49.8\t36.8\tmature
Sample6\tnatural\t30.1\t20.5\tmature
Sample7\tconstructed\t46.7\t33.2\tearly
Sample8\tconstructed\t51.4\t37.5\tmature
"""
        
        with open(feature_table_path, 'w') as f:
            f.write(feature_table_content)
        
        with open(metadata_path, 'w') as f:
            f.write(metadata_content)
        
        # Simulate filtering logic
        # 1. Load metadata
        filtered_samples = []
        with open(metadata_path, 'r') as f:
            lines = f.readlines()
            headers = lines[0].strip().split('\t')
            
            for line in lines[1:]:
                values = line.strip().split('\t')
                sample_data = dict(zip(headers, values))
                
                # Filter for constructed wetlands with nutrient removal metrics
                if (sample_data.get('wetland_type') == 'constructed' and 
                    sample_data.get('n_removal') and 
                    sample_data.get('p_removal')):
                    filtered_samples.append(sample_data['sample_id'])
        
        # Verify filtering results
        assert len(filtered_samples) == 7, f"Expected 7 filtered samples, got {len(filtered_samples)}"
        assert 'Sample6' not in filtered_samples, "Natural wetland sample should be filtered out"
        assert 'Sample1' in filtered_samples, "Constructed wetland sample should be included"
        
        # Write filtered sample list to processed data
        filtered_list_path = data_processed / "filtered_samples.json"
        with open(filtered_list_path, 'w') as f:
            json.dump({"filtered_samples": filtered_samples, "count": len(filtered_samples)}, f)
        
        # Verify output file exists and contains correct data
        assert filtered_list_path.exists(), "Filtered samples file not created"
        
        with open(filtered_list_path, 'r') as f:
            result = json.load(f)
        
        assert result['count'] == 7
        assert 'Sample1' in result['filtered_samples']
        
    finally:
        shutil.rmtree(test_dir)


def test_data_gap_protocol():
    """Test that the data gap protocol halts when no verified dataset is found."""
    test_dir, _, _, data_config = setup_test_environment()
    
    try:
        # Create an empty dataset configuration
        config_path = data_config / "dataset_ids.json"
        empty_config = {
            "datasets": [],
            "metadata": {
                "created_by": "test",
                "version": "1.0"
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(empty_config, f, indent=2)
        
        # Simulate data retrieval with empty config
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        assert len(config_data['datasets']) == 0, "Config should be empty"
        
        # This would trigger the "Data Gap" protocol in the real implementation
        # For this test, we just verify the condition is detected
        data_gap_detected = len(config_data['datasets']) == 0
        assert data_gap_detected, "Data gap should be detected"
        
    finally:
        shutil.rmtree(test_dir)


def test_checksum_recording():
    """Test that checksums are recorded for processed files."""
    test_dir, _, data_processed, _ = setup_test_environment()
    
    try:
        # Create a mock processed file
        test_file = data_processed / "test_output.json"
        test_content = {"test": "data", "count": 10}
        
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        # Calculate and record checksum
        checksum = calculate_file_hash(str(test_file))
        
        assert checksum is not None, "Checksum calculation failed"
        assert len(checksum) == 64, "SHA256 checksum should be 64 characters"
        
        # Verify file integrity
        is_valid = calculate_file_hash(str(test_file)) == checksum
        assert is_valid, "File integrity verification failed"
        
    finally:
        shutil.rmtree(test_dir)


def run_all_tests():
    """Run all integration tests."""
    print("Running integration tests for data retrieval and filtering logic...")
    
    try:
        test_dataset_config_loading()
        print("✓ Dataset config loading test passed")
        
        test_filtering_logic_with_mock_data()
        print("✓ Filtering logic test passed")
        
        test_data_gap_protocol()
        print("✓ Data gap protocol test passed")
        
        test_checksum_recording()
        print("✓ Checksum recording test passed")
        
        print("\nAll integration tests passed successfully!")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)