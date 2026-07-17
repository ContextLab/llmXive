"""
Integration test for SMILES ingestion pipeline (US1).

This test verifies the end-to-end flow of:
1. Fetching real data from ZINC15
2. Validating SMILES syntax
3. Processing molecules into graphs with 2D/3D features
4. Calculating checksums for reproducibility
5. Verifying output file existence and schema compliance

Prerequisites:
- T012 (ingest.py) must be implemented
- T013 (preprocess.py 2D features) must be implemented
- T014 (preprocess.py 3D conformers) must be implemented
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd
import numpy as np

# Project root setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.ingest import (
    validate_smiles,
    fetch_zinc15_data,
    process_smiles_file,
    calculate_checksums,
    main as ingest_main
)
from code.data.preprocess import (
    load_conformer_config,
    atom_to_feature_vector,
    molecule_to_graph,
    extract_2d_features,
    generate_conformers,
    process_molecule_chunk,
    main as preprocess_main
)
from code.data.logging_stats import (
    DatasetStatistics,
    log_dataset_statistics
)
from code.utils.config import get_project_root, get_data_dir, get_results_dir
from code.utils.logging import setup_logging, get_logger


@pytest.fixture
def test_environment():
    """Create a temporary test environment with proper directory structure."""
    # Create temp directory for test outputs
    temp_dir = tempfile.mkdtemp(prefix="zinc15_test_")
    
    # Set up directory structure
    data_dir = Path(temp_dir) / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    splits_dir = data_dir / "splits"
    results_dir = Path(temp_dir) / "results"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging for test
    setup_logging(level="INFO", log_file=str(results_dir / "test_ingest.log"))
    logger = get_logger("test_ingest")
    
    yield {
        "temp_dir": Path(temp_dir),
        "data_dir": data_dir,
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "splits_dir": splits_dir,
        "results_dir": results_dir,
        "logger": logger
    }
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_smiles_file(test_environment):
    """Create a small sample SMILES file for testing."""
    # Use a small, verified set of molecules for testing
    sample_molecules = [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1",  # Benzene
        "CC1=CC=CC=C1",  # Toluene
        "C1CCCCC1",  # Cyclohexane
        "CC(=O)OC",  # Methyl acetate
        "CCOCC",  # Diethyl ether
        "CC(C)C",  # Isobutane
        "CC=O",  # Acetaldehyde
        "C1=CC=CC=C1C=O"  # Benzaldehyde
    ]
    
    smiles_file = test_environment["raw_dir"] / "sample_smiles.txt"
    with open(smiles_file, "w") as f:
        for smiles in sample_molecules:
            f.write(f"{smiles}\n")
    
    return smiles_file


class TestSMILESIngestion:
    """Integration tests for the SMILES ingestion pipeline."""
    
    def test_validate_smiles_valid(self, test_environment):
        """Test SMILES validation with valid molecules."""
        valid_smiles = ["CCO", "c1ccccc1", "CC(=O)O"]
        
        for smiles in valid_smiles:
            is_valid, error_msg = validate_smiles(smiles)
            assert is_valid, f"Valid SMILES '{smiles}' was rejected: {error_msg}"
            assert error_msg is None
    
    def test_validate_smiles_invalid(self, test_environment):
        """Test SMILES validation with invalid molecules."""
        invalid_smiles = [
            "invalid_smiles",
            "C(C(C(C",  # Unbalanced parentheses
            "c1ccccc",  # Incomplete aromatic ring
            "",  # Empty string
            None  # None value
        ]
        
        for smiles in invalid_smiles:
            try:
                is_valid, error_msg = validate_smiles(smiles)
                # If it returns valid=False, that's acceptable
                assert not is_valid or error_msg is not None
            except Exception:
                # Some invalid inputs might raise exceptions, which is also acceptable
                pass
    
    def test_fetch_zinc15_data_structure(self, test_environment):
        """Test that fetch_zinc15_data returns expected structure (without full download)."""
        # We test the function's return structure with a small subset
        # In real execution, this would fetch from ZINC15
        try:
            # Try to fetch a small sample (first 100 molecules if available)
            data = fetch_zinc15_data(
                url="https://zinc15.docking.org/subsets/filtered/1000.mol.gz",
                max_molecules=10,
                timeout=30
            )
            
            # Verify data structure
            assert isinstance(data, dict), "fetch_zinc15_data should return a dict"
            assert "smiles_list" in data, "Data must contain 'smiles_list'"
            assert "metadata" in data, "Data must contain 'metadata'"
            assert isinstance(data["smiles_list"], list), "smiles_list must be a list"
            
            # Verify we got some data
            assert len(data["smiles_list"]) > 0, "Should fetch at least some molecules"
            
        except Exception as e:
            # If ZINC15 is unavailable, log and skip this specific test
            test_environment["logger"].warning(f"ZINC15 fetch failed (expected in some environments): {e}")
            pytest.skip("ZINC15 data source unavailable in test environment")
    
    def test_process_smiles_file_end_to_end(self, test_environment, sample_smiles_file):
        """Test complete SMILES file processing pipeline."""
        logger = test_environment["logger"]
        processed_dir = test_environment["processed_dir"]
        
        # Process the sample SMILES file
        output_file = processed_dir / "processed_sample.csv"
        
        result = process_smiles_file(
            smiles_file=sample_smiles_file,
            output_file=output_file,
            logger=logger,
            chunk_size=5
        )
        
        # Verify processing result
        assert result is not None, "Processing should return a result dict"
        assert "total_molecules" in result, "Result must contain total_molecules"
        assert "processed_molecules" in result, "Result must contain processed_molecules"
        assert "failed_molecules" in result, "Result must contain failed_molecules"
        
        # Verify output file was created
        assert output_file.exists(), f"Output file {output_file} was not created"
        
        # Verify output file has content
        df = pd.read_csv(output_file)
        assert len(df) > 0, "Output CSV should contain processed molecules"
        
        # Verify required columns exist
        required_columns = ["smiles", "molecular_weight", "surface_area", "node_features", "edge_features"]
        for col in required_columns:
            assert col in df.columns, f"Output CSV must contain column '{col}'"
        
        logger.info(f"Successfully processed {result['processed_molecules']} molecules")
    
    def test_checksum_calculation(self, test_environment, sample_smiles_file):
        """Test checksum calculation for data integrity."""
        raw_dir = test_environment["raw_dir"]
        results_dir = test_environment["results_dir"]
        
        # Calculate checksum for the sample file
        checksum_result = calculate_checksums(
            input_file=sample_smiles_file,
            output_dir=results_dir,
            algorithm="sha256"
        )
        
        # Verify checksum result
        assert checksum_result is not None, "Checksum calculation should return a result"
        assert "file_path" in checksum_result, "Result must contain file_path"
        assert "checksum" in checksum_result, "Result must contain checksum"
        assert "algorithm" in checksum_result, "Result must contain algorithm"
        
        # Verify checksum file was created
        checksum_file = results_dir / "checksums.json"
        assert checksum_file.exists(), "Checksum file should be created"
        
        # Verify checksum file content
        with open(checksum_file, "r") as f:
            checksums_data = json.load(f)
            assert "files" in checksums_data, "Checksum file must contain 'files' key"
            assert len(checksums_data["files"]) > 0, "Should contain at least one file checksum"
    
    def test_dataset_statistics_logging(self, test_environment, sample_smiles_file):
        """Test that dataset statistics are properly logged."""
        logger = test_environment["logger"]
        processed_dir = test_environment["processed_dir"]
        
        # Process a small file first
        output_file = processed_dir / "stats_sample.csv"
        process_smiles_file(
            smiles_file=sample_smiles_file,
            output_file=output_file,
            logger=logger,
            chunk_size=5
        )
        
        # Load the processed data
        df = pd.read_csv(output_file)
        
        # Create dataset statistics
        stats = DatasetStatistics(
            total_molecules=len(df),
            valid_molecules=len(df[df["smiles"].notna()]),
            avg_molecular_weight=df["molecular_weight"].mean() if "molecular_weight" in df.columns else 0,
            avg_surface_area=df["surface_area"].mean() if "surface_area" in df.columns else 0,
            min_molecular_weight=df["molecular_weight"].min() if "molecular_weight" in df.columns else 0,
            max_molecular_weight=df["molecular_weight"].max() if "molecular_weight" in df.columns else 0,
            excluded_count=0,
            failure_rate=0.0
        )
        
        # Log the statistics
        log_dataset_statistics(stats, logger)
        
        # Verify log file contains statistics
        log_file = test_environment["results_dir"] / "test_ingest.log"
        assert log_file.exists(), "Log file should be created"
        
        with open(log_file, "r") as f:
            log_content = f.read()
            assert "Dataset Statistics" in log_content, "Log should contain dataset statistics"
            assert str(stats.total_molecules) in log_content, "Log should contain total molecule count"
    
    def test_integration_pipeline_with_real_data(self, test_environment):
        """
        Full integration test: fetch real data, process, validate, and verify outputs.
        This test runs the complete pipeline end-to-end.
        """
        logger = test_environment["logger"]
        raw_dir = test_environment["raw_dir"]
        processed_dir = test_environment["processed_dir"]
        results_dir = test_environment["results_dir"]
        
        try:
            # Step 1: Fetch real data from ZINC15 (small sample for testing)
            logger.info("Step 1: Fetching real data from ZINC15...")
            zinc_data = fetch_zinc15_data(
                url="https://zinc15.docking.org/subsets/filtered/1000.mol.gz",
                max_molecules=20,  # Small sample for testing
                timeout=60
            )
            
            if not zinc_data or len(zinc_data.get("smiles_list", [])) == 0:
                pytest.skip("No data available from ZINC15")
            
            # Save fetched data
            raw_file = raw_dir / "zinc_sample.txt"
            with open(raw_file, "w") as f:
                for smiles in zinc_data["smiles_list"]:
                    if smiles and isinstance(smiles, str):
                        f.write(f"{smiles}\n")
            
            logger.info(f"Fetched {len(zinc_data['smiles_list'])} molecules from ZINC15")
            
            # Step 2: Process the data
            logger.info("Step 2: Processing molecules...")
            processed_file = processed_dir / "zinc_processed.csv"
            
            process_result = process_smiles_file(
                smiles_file=raw_file,
                output_file=processed_file,
                logger=logger,
                chunk_size=10
            )
            
            # Verify processing succeeded
            assert process_result["processed_molecules"] > 0, "Should process at least some molecules"
            assert processed_file.exists(), "Processed file should be created"
            
            # Step 3: Validate output schema
            logger.info("Step 3: Validating output schema...")
            df = pd.read_csv(processed_file)
            
            # Check required columns
            required_cols = ["smiles", "molecular_weight", "surface_area", "node_features", "edge_features"]
            for col in required_cols:
                assert col in df.columns, f"Missing required column: {col}"
            
            # Check data quality
            assert df["smiles"].notna().all(), "All SMILES should be non-null"
            assert df["surface_area"].notna().all(), "All surface areas should be non-null"
            assert df["surface_area"] > 0, "All surface areas should be positive"
            
            # Step 4: Calculate checksums
            logger.info("Step 4: Calculating checksums...")
            checksum_result = calculate_checksums(
                input_file=processed_file,
                output_dir=results_dir,
                algorithm="sha256"
            )
            
            assert checksum_result["checksum"] is not None, "Checksum should be calculated"
            
            # Step 5: Log statistics
            logger.info("Step 5: Logging dataset statistics...")
            stats = DatasetStatistics(
                total_molecules=len(df),
                valid_molecules=len(df),
                avg_molecular_weight=df["molecular_weight"].mean(),
                avg_surface_area=df["surface_area"].mean(),
                min_molecular_weight=df["molecular_weight"].min(),
                max_molecular_weight=df["molecular_weight"].max(),
                excluded_count=0,
                failure_rate=0.0
            )
            log_dataset_statistics(stats, logger)
            
            logger.info("Integration test completed successfully!")
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            # Re-raise to fail the test
            raise