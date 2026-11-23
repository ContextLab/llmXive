import json
import os
import tempfile
import unittest
from pathlib import Path
import yaml

# Mock the validation module functions if they are not fully implemented yet,
# or import them if they are. For T033, we focus on the runner logic.
# We assume run_schema_validation and save_validation_report exist in validation.py
# as per the API surface provided.

class TestSchemaValidationRunner(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / "data"
        self.data_dir.mkdir(parents=True)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.contracts_dir = self.data_dir / "contracts"
        
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.contracts_dir.mkdir()

        self.raw_data_path = self.raw_dir / "participant_logs.json"
        self.schema_path = self.contracts_dir / "dataset.schema.yaml"
        self.output_path = self.processed_dir / "validation_report.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_valid_schema(self):
        schema = {
            "type": "object",
            "required": ["participant_id", "condition", "status"],
            "properties": {
                "participant_id": {"type": "string"},
                "condition": {"type": "string", "enum": ["LLM", "Human", "None"]},
                "status": {"type": "string", "enum": ["complete", "incomplete"]},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "help_request_count": {"type": "integer"},
                "cognitive_load_proxy": {"type": "number"},
                "subjective_rating": {"type": "number"}
            }
        }
        with open(self.schema_path, 'w') as f:
            yaml.dump(schema, f)

    def create_valid_data(self):
        data = [
            {
                "participant_id": "uuid-1234",
                "condition": "LLM",
                "status": "complete",
                "start_time": "2023-01-01T10:00:00Z",
                "end_time": "2023-01-01T10:30:00Z",
                "help_request_count": 2,
                "cognitive_load_proxy": 0.5,
                "subjective_rating": 4.0
            },
            {
                "participant_id": "uuid-5678",
                "condition": "Human",
                "status": "incomplete",
                "start_time": "2023-01-01T11:00:00Z",
                "end_time": None,
                "help_request_count": 5,
                "cognitive_load_proxy": 0.8,
                "subjective_rating": 2.0
            }
        ]
        with open(self.raw_data_path, 'w') as f:
            json.dump(data, f)

    def create_invalid_data(self):
        # Missing required field 'condition'
        data = [
            {
                "participant_id": "uuid-1234",
                "status": "complete"
            }
        ]
        with open(self.raw_data_path, 'w') as f:
            json.dump(data, f)

    def test_valid_data_passes(self):
        self.create_valid_schema()
        self.create_valid_data()
        
        # Change to temp dir to simulate project root
        old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        try:
            # Import and run the main function logic
            # We need to mock sys.exit to prevent the test from stopping
            import sys
            original_exit = sys.exit
            sys.exit = lambda code: None
            
            from run_schema_validation import main
            main()
            
            sys.exit = original_exit

            # Check output
            self.assertTrue(self.output_path.exists())
            with open(self.output_path, 'r') as f:
                report = json.load(f)
            
            self.assertTrue(report['is_valid'])
            self.assertEqual(report['gate_status'], 'PASS')
            self.assertEqual(len(report['errors']), 0)
        finally:
            os.chdir(old_cwd)

    def test_invalid_data_fails_gate(self):
        self.create_valid_schema()
        self.create_invalid_data()
        
        old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        try:
            import sys
            original_exit = sys.exit
            exit_code = [None]
            def mock_exit(code):
                exit_code[0] = code
                raise SystemExit(code)
            sys.exit = mock_exit
            
            from run_schema_validation import main
            
            with self.assertRaises(SystemExit):
                main()
            
            self.assertEqual(exit_code[0], 1)
            
            # Check output exists even on failure (report of failure)
            self.assertTrue(self.output_path.exists())
            with open(self.output_path, 'r') as f:
                report = json.load(f)
            
            self.assertFalse(report['is_valid'])
            self.assertEqual(report['gate_status'], 'ABORT')
            self.assertGreater(len(report['errors']), 0)
        finally:
            sys.exit = original_exit
            os.chdir(old_cwd)

    def test_missing_data_file_aborts(self):
        self.create_valid_schema()
        # Do not create data file
        
        old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        try:
            import sys
            original_exit = sys.exit
            exit_code = [None]
            def mock_exit(code):
                exit_code[0] = code
                raise SystemExit(code)
            sys.exit = mock_exit
            
            from run_schema_validation import main
            
            with self.assertRaises(SystemExit):
                main()
            
            self.assertEqual(exit_code[0], 1)
        finally:
            sys.exit = original_exit
            os.chdir(old_cwd)

    def test_missing_schema_file_aborts(self):
        self.create_valid_data()
        # Do not create schema file
        
        old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        try:
            import sys
            original_exit = sys.exit
            exit_code = [None]
            def mock_exit(code):
                exit_code[0] = code
                raise SystemExit(code)
            sys.exit = mock_exit
            
            from run_schema_validation import main
            
            with self.assertRaises(SystemExit):
                main()
            
            self.assertEqual(exit_code[0], 1)
        finally:
            sys.exit = original_exit
            os.chdir(old_cwd)

if __name__ == '__main__':
    unittest.main()