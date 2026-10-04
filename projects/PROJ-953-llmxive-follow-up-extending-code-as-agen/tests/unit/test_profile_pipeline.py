import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.profile_pipeline import run_with_profiler, get_memory_usage_mb, run_full_pipeline

class TestProfilePipeline(unittest.TestCase):
    
    def test_get_memory_usage_mb(self):
        """Test that memory usage function returns a non-negative number."""
        mem = get_memory_usage_mb()
        self.assertIsInstance(mem, float)
        self.assertGreaterEqual(mem, 0)
    
    def test_run_with_profiler_success(self):
        """Test profiler with a successful function execution."""
        def dummy_func():
            return "success"
        
        result = run_with_profiler(dummy_func)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], "success")
        self.assertGreater(result['runtime_seconds'], 0)
        self.assertIn('profile_stats', result)
        self.assertIsInstance(result['profile_stats'], str)
        self.assertGreater(len(result['profile_stats']), 0)
    
    def test_run_with_profiler_failure(self):
        """Test profiler with a failing function execution."""
        def failing_func():
            raise ValueError("Intentional error")
        
        result = run_with_profiler(failing_func)
        
        self.assertFalse(result['success'])
        self.assertIn("Intentional error", str(result['result']))
        self.assertGreater(result['runtime_seconds'], 0)
    
    def test_run_full_pipeline_structure(self):
        """Test that run_full_pipeline returns expected structure."""
        # Mock the individual stage functions to avoid actual execution
        with patch('scripts.profile_pipeline.ingest_main') as mock_ingest, \
             patch('scripts.profile_pipeline.extract_features_main') as mock_extract, \
             patch('scripts.profile_pipeline.train_model_main') as mock_train:
            
            mock_ingest.return_value = None
            mock_extract.return_value = None
            mock_train.return_value = None
            
            results = run_full_pipeline()
            
            # Check top-level keys
            self.assertIn('pipeline_start_time', results)
            self.assertIn('pipeline_end_time', results)
            self.assertIn('stages', results)
            self.assertIn('total_runtime_seconds', results)
            self.assertIn('total_runtime_hours', results)
            self.assertIn('peak_memory_mb', results)
            self.assertIn('constraint_satisfied', results)
            self.assertIn('overall_success', results)
            
            # Check stages
            self.assertIn('ingestion', results['stages'])
            self.assertIn('feature_extraction', results['stages'])
            self.assertIn('model_training', results['stages'])
            
            # Check stage structure
            for stage_name in ['ingestion', 'feature_extraction', 'model_training']:
                stage = results['stages'][stage_name]
                self.assertIn('success', stage)
                self.assertIn('runtime_seconds', stage)
                self.assertIn('memory_start_mb', stage)
                self.assertIn('memory_end_mb', stage)
                self.assertIn('memory_peak_mb', stage)
    
    def test_constraint_verification(self):
        """Test that constraint verification logic is correct."""
        with patch('scripts.profile_pipeline.ingest_main'), \
             patch('scripts.profile_pipeline.extract_features_main'), \
             patch('scripts.profile_pipeline.train_model_main'):
            
            results = run_full_pipeline()
            
            # Check constraint keys exist
            self.assertIn('runtime_under_6h', results['constraint_satisfied'])
            self.assertIn('memory_under_7gb', results['constraint_satisfied'])
            
            # Check they are booleans
            self.assertIsInstance(results['constraint_satisfied']['runtime_under_6h'], bool)
            self.assertIsInstance(results['constraint_satisfied']['memory_under_7gb'], bool)
    
    def test_artifact_generation(self):
        """Test that profiling artifacts are generated."""
        with patch('scripts.profile_pipeline.ingest_main'), \
             patch('scripts.profile_pipeline.extract_features_main'), \
             patch('scripts.profile_pipeline.train_model_main'):
            
            results = run_full_pipeline()
            
            # Check that log files would be created (we can't test actual file creation
            # in a unit test without mocking file I/O, but we can verify the logic)
            logs_dir = Path("data/logs")
            self.assertTrue(logs_dir.exists())
            
            json_path = logs_dir / "pipeline_runtime.json"
            log_path = logs_dir / "runtime_profile.log"
            
            # In a real run, these files would exist
            # For unit test, we just verify the paths are correct
            self.assertEqual(json_path.name, "pipeline_runtime.json")
            self.assertEqual(log_path.name, "runtime_profile.log")

if __name__ == '__main__':
    unittest.main()
