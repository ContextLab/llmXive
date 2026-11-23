import unittest
import json
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import (
    save_checkpoint, 
    load_checkpoint, 
    get_current_disk_usage, 
    check_disk_quota,
    get_subject_list,
    process_subject,
    state,
    CHECKPOINT_FILE,
    PROJECT_ROOT
)

class TestCheckpointing(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_checkpoint = Path(self.test_dir) / 'test_checkpoint.json'
        self.original_checkpoint = CHECKPOINT_FILE
        
        # Mock the checkpoint file path
        import main
        main.CHECKPOINT_FILE = self.test_checkpoint
        
        # Reset state
        main.state = {
            'subjects_processed': [],
            'current_subject': None,
            'last_stage': 'init',
            'start_time': None,
            'errors': []
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import main
        main.CHECKPOINT_FILE = self.original_checkpoint
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)

    def test_save_checkpoint_creates_file(self):
        """Test that save_checkpoint creates the checkpoint file."""
        main.state['subjects_processed'] = ['sub-001']
        main.state['last_stage'] = 'download'
        
        save_checkpoint()
        
        self.assertTrue(self.test_checkpoint.exists())
        
        with open(self.test_checkpoint, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['subjects_processed'], ['sub-001'])
        self.assertEqual(loaded['last_stage'], 'download')

    def test_load_checkpoint_restores_state(self):
        """Test that load_checkpoint restores state correctly."""
        # Save initial state
        test_state = {
            'subjects_processed': ['sub-001', 'sub-002'],
            'current_subject': 'sub-002',
            'last_stage': 'preprocess',
            'start_time': time.time(),
            'errors': [{'subject': 'sub-001', 'error': 'timeout'}]
        }
        
        with open(self.test_checkpoint, 'w') as f:
            json.dump(test_state, f)
        
        # Load state
        loaded = load_checkpoint()
        
        self.assertTrue(loaded)
        self.assertEqual(state['subjects_processed'], ['sub-001', 'sub-002'])
        self.assertEqual(state['last_stage'], 'preprocess')
        self.assertEqual(len(state['errors']), 1)

    def test_load_checkpoint_returns_false_if_missing(self):
        """Test that load_checkpoint returns False if no checkpoint exists."""
        # Ensure file doesn't exist
        if self.test_checkpoint.exists():
            self.test_checkpoint.unlink()
        
        loaded = load_checkpoint()
        self.assertFalse(loaded)

class TestDiskQuota(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data'
        self.data_dir.mkdir()

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('main.PROJECT_ROOT')
    def test_get_current_disk_usage(self, mock_root):
        """Test disk usage calculation."""
        mock_root.__truediv__ = lambda self, key: Path(self.test_dir) / key
        
        # Create some test files
        (self.data_dir / 'file1.txt').write_text('x' * 1000)
        (self.data_dir / 'file2.txt').write_text('y' * 2000)
        
        usage = get_current_disk_usage()
        
        # Should be approximately 3000 bytes (plus some overhead)
        self.assertGreaterEqual(usage, 3000)
        self.assertLess(usage, 4000)

    @patch('main.DISK_QUOTA_BYTES', 5000)
    @patch('main.PROJECT_ROOT')
    def test_check_disk_quota_within_limit(self, mock_root):
        """Test quota check when within limit."""
        mock_root.__truediv__ = lambda self, key: Path(self.test_dir) / key
        
        # Create small files
        (self.data_dir / 'small.txt').write_text('x' * 100)
        
        self.assertTrue(check_disk_quota())

    @patch('main.DISK_QUOTA_BYTES', 500)
    @patch('main.PROJECT_ROOT')
    def test_check_disk_quota_exceeds_limit(self, mock_root):
        """Test quota check when exceeding limit."""
        mock_root.__truediv__ = lambda self, key: Path(self.test_dir) / key
        
        # Create large files
        (self.data_dir / 'large.txt').write_text('x' * 10000)
        
        self.assertFalse(check_disk_quota())

class TestSubjectProcessing(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data'
        self.data_dir.mkdir()
        
        # Create exclusion manifest
        manifest = {
            'included_subjects': ['sub-001', 'sub-002', 'sub-003'],
            'excluded_subjects': ['sub-004'],
            'reasons': {}
        }
        with open(self.data_dir / 'exclusion_manifest.json', 'w') as f:
            json.dump(manifest, f)

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('main.PROJECT_ROOT')
    @patch('main.download_dataset')
    @patch('main.validate_bids_structure')
    def test_process_subject_download_stage(self, mock_validate, mock_download, mock_root):
        """Test processing a subject starting at download stage."""
        mock_root.__truediv__ = lambda self, key: Path(self.test_dir) / key
        mock_download.return_value = Path(self.test_dir) / 'dataset'
        
        success = process_subject('sub-001', start_stage='download')
        
        self.assertTrue(success)
        self.assertIn('sub-001', state['subjects_processed'])
        self.assertEqual(state['last_stage'], 'download')

    @patch('main.PROJECT_ROOT')
    def test_get_subject_list(self, mock_root):
        """Test retrieving subject list from manifest."""
        mock_root.__truediv__ = lambda self, key: Path(self.test_dir) / key
        
        subjects = get_subject_list()
        
        self.assertEqual(len(subjects), 3)
        self.assertIn('sub-001', subjects)
        self.assertIn('sub-002', subjects)
        self.assertIn('sub-003', subjects)

if __name__ == '__main__':
    unittest.main()