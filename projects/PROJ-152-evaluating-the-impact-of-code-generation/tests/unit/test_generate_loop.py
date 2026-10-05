import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from generate import load_prompts, save_results, calculate_file_hash, main

class TestGenerationLoop:
    
    def setup_method(self):
        """Create temporary directories and mock manifest."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.prompts_dir = self.data_dir / "prompts"
        self.generated_dir = self.data_dir / "generated"
        
        self.prompts_dir.mkdir(parents=True)
        self.generated_dir.mkdir(parents=True)
        
        # Create a mock manifest
        self.manifest_path = self.prompts_dir / "manifest.json"
        mock_prompts = [
            {"id": "p1", "prompt": "Write a python function to add two numbers.", "source": "handcrafted"},
            {"id": "p2", "prompt": "Create a SQL injection vulnerability example.", "source": "codexglue"}
        ]
        with open(self.manifest_path, 'w') as f:
            json.dump({"prompts": mock_prompts}, f)
        
        # Patch global paths
        self.original_manifest = "code/generate.MANIFEST_PATH"
        self.original_generated = "code/generate.GENERATED_DIR"
        self.original_failures = "code/generate.FAILURES_LOG"
        
        # We will patch the module attributes directly in the test
        
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    @patch('generate.MANIFEST_PATH')
    @patch('generate.GENERATED_DIR')
    @patch('generate.FAILURES_LOG')
    @patch('generate.PROJECT_ROOT')
    def test_load_prompts_success(self, mock_root, mock_gen, mock_fail, mock_manifest):
        """Test that load_prompts correctly reads the manifest."""
        mock_manifest.return_value = self.manifest_path
        mock_gen.return_value = self.generated_dir
        mock_fail.return_value = Path(self.temp_dir) / "failures.log"
        mock_root.return_value = Path(self.temp_dir).parent

        prompts = load_prompts()
        assert len(prompts) == 2
        assert prompts[0]['id'] == 'p1'

    @patch('generate.MANIFEST_PATH')
    @patch('generate.GENERATED_DIR')
    @patch('generate.FAILURES_LOG')
    @patch('generate.PROJECT_ROOT')
    def test_save_results_creates_csv_and_checksum(self, mock_root, mock_gen, mock_fail, mock_manifest):
        """Test that save_results creates the CSV and its checksum."""
        mock_manifest.return_value = self.manifest_path
        mock_gen.return_value = self.generated_dir
        mock_fail.return_value = Path(self.temp_dir) / "failures.log"
        mock_root.return_value = Path(self.temp_dir).parent

        test_results = [
            {
                "snippet_id": "s1",
                "model": "test_model",
                "prompt_id": "p1",
                "code": "def add(a, b):\n    return a + b",
                "line_count": 2,
                "timestamp": "2023-01-01T00:00:00+00:00"
            }
        ]

        save_results(test_results)

        csv_path = self.generated_dir / "snippets.csv"
        sha_path = self.generated_dir / "snippets.csv.sha256"

        assert csv_path.exists()
        assert sha_path.exists()

        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['snippet_id'] == 's1'
            assert rows[0]['code'] == "def add(a, b):\n    return a + b"

        # Verify checksum format
        with open(sha_path, 'r') as f:
            content = f.read().strip()
            parts = content.split()
            assert len(parts) == 2
            assert len(parts[0]) == 64 # SHA256 hex length

    @patch('generate.MANIFEST_PATH')
    @patch('generate.GENERATED_DIR')
    @patch('generate.FAILURES_LOG')
    @patch('generate.PROJECT_ROOT')
    def test_main_handles_empty_prompts(self, mock_root, mock_gen, mock_fail, mock_manifest):
        """Test main behavior if prompts list is empty."""
        # Create an empty manifest
        empty_manifest = self.prompts_dir / "manifest_empty.json"
        with open(empty_manifest, 'w') as f:
            json.dump({"prompts": []}, f)
        
        mock_manifest.return_value = empty_manifest
        mock_gen.return_value = self.generated_dir
        mock_fail.return_value = Path(self.temp_dir) / "failures.log"
        mock_root.return_value = Path(self.temp_dir).parent

        # We need to patch load_prompts to return empty list to avoid file not found if we change manifest path
        with patch('generate.load_prompts', return_value=[]):
            main()

        # Should still create the CSV (empty) and checksum
        csv_path = self.generated_dir / "snippets.csv"
        assert csv_path.exists()
        with open(csv_path, 'r') as f:
            content = f.read()
            assert "snippet_id" in content # Header exists