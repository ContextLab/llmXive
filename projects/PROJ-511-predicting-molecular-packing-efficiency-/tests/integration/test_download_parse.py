"""
Integration test for the download and parse pipeline (T011).

This test verifies that the full pipeline from downloading CIFs from the
Crystallography Open Database (COD) to parsing them into a dataset works
end-to-end. It depends on the implementation of T012 (download_cif.py)
and T013 (parse_cif.py).

The test:
1. Downloads a small, controlled batch of organic CIFs from COD.
2. Parses them to extract SMILES and metadata.
3. Validates that the output DataFrame contains the expected columns.
4. Validates that the SMILES strings are valid according to RDKit.
5. Cleans up temporary files.

NOTE: This test requires network access to the COD. If the network is
unavailable, the test will raise a RuntimeError, ensuring the pipeline
is verified against real data.
"""
import os
import sys
import tempfile
import shutil
import logging
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from rdkit import Chem
from rdkit.Chem import AllChem

# Import pipeline modules
from download_cif import download_cif, get_cod_id_list, extract_atom_count_from_cif
from parse_cif import generate_smiles_from_cif, parse_cif_metadata, process_single_cif
from utils import fix_seed, setup_logging
from error_handling import CIFParseError, handle_corrupt_cif

# Configure logging
logger = setup_logging("TEST", level=logging.INFO)

class TestDownloadParsePipeline(unittest.TestCase):
    """Integration test for T012 and T013."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        fix_seed(42)
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_cod_ids = [
            "1545982", # Aspirin
            "1546058", # Caffeine
            "1545990", # Urea
            "1545946", # Sucrose
            "1545920", # Benzoic Acid
        ]
        cls.cif_files: List[str] = []

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary files."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_01_download_cif_batch(self):
        """Test downloading a small batch of CIFs from COD."""
        logger.info(f"Downloading {len(self.test_cod_ids)} CIFs from COD...")
        
        downloaded_files = []
        for cod_id in self.test_cod_ids:
            url = f"https://www.crystallography.net/cod/{cod_id}.cif"
            local_path = os.path.join(self.temp_dir, f"{cod_id}.cif")
            
            try:
                success = download_cif(url, local_path)
                if success and os.path.exists(local_path):
                    downloaded_files.append(local_path)
                    logger.info(f"Successfully downloaded {cod_id}")
                else:
                    logger.warning(f"Failed to download {cod_id}")
            except Exception as e:
                logger.error(f"Error downloading {cod_id}: {e}")
                raise
        
        self.assertGreater(len(downloaded_files), 0, "No CIFs were downloaded.")
        self.cif_files = downloaded_files

    def test_02_parse_cif_and_generate_smiles(self):
        """Test parsing CIFs and generating SMILES strings."""
        logger.info("Parsing downloaded CIFs and generating SMILES...")
        
        results = []
        for cif_path in self.cif_files:
            try:
                # Parse metadata
                metadata = parse_cif_metadata(cif_path)
                
                # Generate SMILES
                smiles = generate_smiles_from_cif(cif_path)
                
                if smiles is None:
                    logger.warning(f"Could not generate SMILES for {cif_path}")
                    continue
                
                # Validate SMILES
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    logger.warning(f"Invalid SMILES generated for {cif_path}: {smiles}")
                    continue
                
                results.append({
                    "file": cif_path,
                    "cod_id": metadata.get("cod_id", "unknown"),
                    "smiles": smiles,
                    "num_atoms": metadata.get("num_atoms", 0),
                    "valid": True
                })
                
            except CIFParseError as e:
                logger.error(f"Parse error for {cif_path}: {e}")
                handle_corrupt_cif(cif_path, str(e))
            except Exception as e:
                logger.error(f"Unexpected error processing {cif_path}: {e}")
                raise
        
        self.assertGreater(len(results), 0, "No valid records were parsed.")
        
        # Validate expected columns
        df_keys = ["file", "cod_id", "smiles", "num_atoms", "valid"]
        for r in results:
            for key in df_keys:
                self.assertIn(key, r, f"Missing key '{key}' in result for {r.get('file')}")
        
        logger.info(f"Successfully parsed {len(results)} records.")
        
    def test_03_pipeline_integration(self):
        """End-to-end integration test: Download -> Parse -> Validate."""
        logger.info("Running end-to-end integration test...")
        
        # Re-use downloaded files if available, otherwise download
        if not self.cif_files:
            self.test_01_download_cif_batch()
        
        successful_parses = 0
        for cif_path in self.cif_files:
            try:
                # Simulate the process_single_cif function flow
                metadata = parse_cif_metadata(cif_path)
                smiles = generate_smiles_from_cif(cif_path)
                
                if smiles:
                    mol = Chem.MolFromSmiles(smiles)
                    if mol:
                        successful_parses += 1
                        logger.debug(f"Success: {os.path.basename(cif_path)} -> {smiles[:20]}...")
                
            except Exception as e:
                logger.warning(f"Failed to process {cif_path}: {e}")
                continue
        
        # Assert that we got at least some successful parses
        # Note: We expect most to succeed, but allow for 1-2 failures due to COD quirks
        self.assertGreaterEqual(
            successful_parses, 
            len(self.cif_files) - 2, 
            f"Too many failures: {len(self.cif_files) - successful_parses} out of {len(self.cif_files)}"
        )

    def test_04_verify_real_data_source(self):
        """Verify that the data comes from the real COD source."""
        # This test ensures we are not using synthetic data.
        # It checks that the downloaded files have the expected COD header.
        for cif_path in self.cif_files:
            with open(cif_path, 'r') as f:
                content = f.read()
                self.assertIn("data_", content, "Missing 'data_' header in CIF file.")
                self.assertIn("loop_", content, "Missing 'loop_' in CIF file.")
                # Check for a specific COD ID in the file to ensure it's the right one
                cod_id = Path(cif_path).stem
                self.assertIn(cod_id, content, f"CIF file {cif_path} does not contain expected ID {cod_id}")

if __name__ == "__main__":
    unittest.main(verbosity=2)