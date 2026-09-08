"""
Unit tests for T019b traceability functionality.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.task019b_traceability import (
    load_checksum_manifest,
    load_single_run_results,
    find_checksum_for_run,
    update_run_metadata,
    save_updated_results
)

class TestTask019bTraceability(TestCase):
    """Tests for T019b traceability functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create test checksum manifest
        self.checksum_manifest = {
            'version': '1.0',
            'created_at': '2024-01-01T00:00:00Z',
            'entries': [
                {
                    'file_path': 'data/raw/matrix_N1000_seed42.npy',
                    'hash': 'abc123def456789',
                    'N': 1000,
                    'seed': 42
                },
                {
                    'file_path': 'data/raw/matrix_N1000_seed123.npy',
                    'hash': 'xyz789abc123456',
                    'N': 1000,
                    'seed': 123
                },
                {
                    'file_path': 'data/raw/matrix_N2000_seed42.npy',
                    'hash': 'def456abc789123',
                    'N': 2000,
                    'seed': 42
                }
            ]
        }
        
        # Create test results file
        self.results = {
            'run_id': 'test-run-001',
            'N': 1000,
            'seed': 42,
            'theta': 2.5,
            'eigenvalues': [2.5, 1.9, 1.8, 1.7],
            'outlier_flag': True
        }

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_checksum_manifest(self):
        """Test loading checksum manifest from file."""
        manifest_path = self.temp_path / 'checksums.json'
        with open(manifest_path, 'w') as f:
            json.dump(self.checksum_manifest, f)
        
        loaded = load_checksum_manifest(manifest_path)
        
        self.assertEqual(loaded['version'], '1.0')
        self.assertEqual(len(loaded['entries']), 3)
        self.assertEqual(loaded['entries'][0]['file_path'], 'data/raw/matrix_N1000_seed42.npy')

    def test_load_single_run_results(self):
        """Test loading single run results from file."""
        results_path = self.temp_path / 'results.json'
        with open(results_path, 'w') as f:
            json.dump(self.results, f)
        
        loaded = load_single_run_results(results_path)
        
        self.assertEqual(loaded['N'], 1000)
        self.assertEqual(loaded['seed'], 42)
        self.assertTrue(loaded['outlier_flag'])

    def test_find_checksum_for_run(self):
        """Test finding checksum for specific run parameters."""
        run_params = {'N': 1000, 'seed': 42, 'theta': 2.5}
        
        checksum = find_checksum_for_run(self.checksum_manifest, run_params)
        
        self.assertEqual(checksum, 'abc123def456789')

    def test_find_checksum_for_run_not_found(self):
        """Test that ValueError is raised when checksum not found."""
        run_params = {'N': 999, 'seed': 999}  # Non-existent params
        
        with self.assertRaises(ValueError):
            find_checksum_for_run(self.checksum_manifest, run_params)

    def test_update_run_metadata(self):
        """Test updating run metadata with checksum information."""
        checksum_hash = 'abc123def456789'
        raw_file = 'data/raw/matrix_N1000_seed42.npy'
        
        updated = update_run_metadata(self.results.copy(), checksum_hash, raw_file)
        
        self.assertIn('traceability', updated)
        self.assertEqual(updated['traceability']['raw_matrix_checksum'], checksum_hash)
        self.assertEqual(updated['traceability']['raw_matrix_file'], raw_file)
        self.assertEqual(updated['traceability']['data_hygiene_status'], 'verified')
        self.assertIn('checksum_timestamp', updated['traceability'])

    def test_save_updated_results(self):
        """Test saving updated results to file."""
        updated_results = {
            'run_id': 'test-run-001',
            'traceability': {
                'raw_matrix_checksum': 'abc123def456789',
                'raw_matrix_file': 'data/raw/matrix_N1000_seed42.npy',
                'data_hygiene_status': 'verified'
            }
        }
        
        output_path = self.temp_path / 'output_results.json'
        save_updated_results(updated_results, output_path)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['traceability']['raw_matrix_checksum'], 'abc123def456789')
        self.assertEqual(loaded['traceability']['data_hygiene_status'], 'verified')

    def test_find_checksum_with_theta_matching(self):
        """Test checksum matching when theta is also specified."""
        checksum_manifest_with_theta = {
            'entries': [
                {
                    'file_path': 'data/raw/matrix_N1000_seed42.npy',
                    'hash': 'hash_theta_2_5',
                    'N': 1000,
                    'seed': 42,
                    'theta': 2.5
                },
                {
                    'file_path': 'data/raw/matrix_N1000_seed42.npy',
                    'hash': 'hash_theta_3_0',
                    'N': 1000,
                    'seed': 42,
                    'theta': 3.0
                }
            ]
        }
        
        # Should match theta=2.5
        checksum = find_checksum_for_run(
            checksum_manifest_with_theta, 
            {'N': 1000, 'seed': 42, 'theta': 2.5}
        )
        
        self.assertEqual(checksum, 'hash_theta_2_5')
        
        # Should match theta=3.0
        checksum = find_checksum_for_run(
            checksum_manifest_with_theta, 
            {'N': 1000, 'seed': 42, 'theta': 3.0}
        )
        
        self.assertEqual(checksum, 'hash_theta_3_0')
