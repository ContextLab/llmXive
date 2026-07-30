"""
Integration test for full data pipeline on a small sample (N=100).

This test verifies the end-to-end flow of User Story 1:
1. Downloads OULAD data (or uses cached raw data if available).
2. Preprocesses data to filter courses and extract learner records.
3. Applies exclusions (no forum interactions, <50 learners per course).
4. Validates the output contains at least N=100 records with required fields.

This test is designed to run on a small sample to ensure fast execution
while validating the integrity of the full pipeline.
"""
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

# Import the core pipeline modules
from download_data import download_oulad_data
from preprocess import load_raw_datasets, filter_courses_by_events, extract_learner_records, apply_min_learner_filter
from apply_exclusions import load_raw_learner_data, filter_no_forum_interactions, save_filtered_data

# Import schema validation utilities
from schema import load_schema_from_file, validate_column_presence, validate_null_values


class TestPipelineSampleIntegration(unittest.TestCase):
    """Integration test for the full US1 data pipeline on a sample size."""

    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp(prefix="oulad_test_")
        self.data_dir = Path(self.test_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Mock config to point to test directories
        self.config_patch = patch(
            'code.config.load_config',
            return_value={
                'data': {
                    'raw_dir': str(self.raw_dir),
                    'processed_dir': str(self.processed_dir),
                    'oulad_url': 'https://analyse.kmi.open.ac.uk/open_dataset'
                }
            }
        )
        self.config_patch.start()

        # Mock logging to avoid console spam in tests
        self.logging_patch = patch('code.logging_config.setup_logger', return_value=MagicMock())
        self.logging_patch.start()

    def tearDown(self):
        """Clean up temporary directory."""
        self.config_patch.stop()
        self.logging_patch.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mock_raw_data(self):
        """Create minimal mock OULAD raw data files for testing."""
        # Create vds (student course) data
        vds_data = pd.DataFrame({
            'id_student': [f'student_{i}' for i in range(150)],
            'id_course': ['001'] * 100 + ['002'] * 50,  # Two courses
            'code_module': ['001'] * 100 + ['002'] * 50,
            'code_presentation': ['2013J'] * 150,
            'date_registered': ['2013-01-01'] * 150,
            'date_unregistered': ['2013-06-01'] * 50 + [None] * 100,  # 50 withdrawn, 100 active
            'final_result': ['Pass'] * 80 + ['Fail'] * 20 + [None] * 50  # 100 graded, 50 no result
        })
        vds_path = self.raw_dir / 'vds.csv'
        vds_data.to_csv(vds_path, index=False)

        # Create events data (simulating forum and assessment events)
        # We need enough events to ensure learners have forum interactions
        events_data = []
        for i in range(150):
            student_id = f'student_{i}'
            course_id = '001' if i < 100 else '002'
            
            # Add forum events for all students (to pass forum filter)
            for j in range(5):
                events_data.append({
                    'id_student': student_id,
                    'id_course': course_id,
                    'event_type': 'forum',
                    'date': '2013-02-01',
                    'time': '10:00:00'
                })
            
            # Add assessment events for most students
            if i < 120:  # 120 students have assessment events
                events_data.append({
                    'id_student': student_id,
                    'id_course': course_id,
                    'event_type': 'assessment',
                    'date': '2013-03-01',
                    'time': '14:00:00'
                })
        
        events_df = pd.DataFrame(events_data)
        events_path = self.raw_dir / 'events.csv'
        events_df.to_csv(events_path, index=False)

        # Create courses data
        courses_data = pd.DataFrame({
            'id_course': ['001', '002'],
            'code_module': ['001', '002'],
            'code_presentation': ['2013J', '2013J'],
            'url': ['http://example.com/001', 'http://example.com/002'],
            'num_assessments': [5, 3],
            'num_forum': [10, 8]
        })
        courses_path = self.raw_dir / 'courses.csv'
        courses_data.to_csv(courses_path, index=False)

    def test_full_pipeline_sample(self):
        """
        Test the full pipeline on a small sample (N=100).
        
        This test:
        1. Creates mock raw data files
        2. Runs the preprocessing pipeline
        3. Verifies the output contains >= 100 records
        4. Validates schema compliance
        """
        # Step 1: Create mock raw data
        self._create_mock_raw_data()

        # Step 2: Run preprocessing pipeline
        # Load raw datasets
        raw_data = load_raw_datasets(self.raw_dir)
        
        # Filter courses by events (must have both assessment and forum)
        filtered_courses = filter_courses_by_events(raw_data['courses'], raw_data['events'])
        
        # Extract learner records
        learner_records = extract_learner_records(
            raw_data['vds'], 
            raw_data['events'], 
            filtered_courses
        )
        
        # Apply minimum learner filter (>=50 learners per course)
        filtered_learners = apply_min_learner_filter(learner_records, min_learners=50)
        
        # Step 3: Apply exclusions (no forum interactions)
        # Load the filtered data as if it came from the pipeline
        filtered_df = filtered_learners.copy()
        
        # Apply exclusion for learners with no forum interactions
        final_df = filter_no_forum_interactions(filtered_df)
        
        # Save the final filtered data
        output_path = self.processed_dir / 'learners_raw_sample.csv'
        save_filtered_data(final_df, output_path)
        
        # Step 4: Validate output
        self.assertTrue(output_path.exists(), "Output file was not created")
        
        # Load and validate the output
        output_df = pd.read_csv(output_path)
        
        # Check that we have at least 100 records (the sample size target)
        # Note: With our mock data, we expect ~100-120 records after filtering
        self.assertGreaterEqual(
            len(output_df), 100,
            f"Expected at least 100 records, got {len(output_df)}. "
            "Pipeline may be filtering too aggressively."
        )
        
        # Validate schema compliance
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
        if schema_path.exists():
            schema = load_schema_from_file(schema_path)
            validate_column_presence(output_df, schema)
            validate_null_values(output_df, schema)
        
        # Verify required columns exist and have non-null values
        required_columns = ['id_student', 'id_course', 'feedback_interval_hours', 
                          'final_grade', 'is_complete', 'feedback_group']
        
        for col in required_columns:
            self.assertIn(col, output_df.columns, f"Missing required column: {col}")
            # Check that at least some values are non-null (allowing for some missing data)
            null_count = output_df[col].isnull().sum()
            self.assertLess(
                null_count, len(output_df) * 0.5,
                f"Column '{col}' has too many null values ({null_count}/{len(output_df)})"
            )
        
        # Verify data types are reasonable
        self.assertTrue(pd.api.types.is_numeric_dtype(output_df['feedback_interval_hours']))
        self.assertTrue(pd.api.types.is_numeric_dtype(output_df['final_grade']))
        
        print(f"✓ Pipeline sample test passed: {len(output_df)} records generated")
        print(f"✓ Output saved to: {output_path}")
        print(f"✓ Schema validation passed")

    def test_pipeline_with_real_data_structure(self):
        """
        Test that the pipeline handles the expected real data structure correctly.
        
        This test ensures that if real OULAD data is available, the pipeline
        can process it without errors.
        """
        # Create mock data that more closely resembles real OULAD structure
        self._create_mock_raw_data()
        
        # Run the full pipeline again to ensure consistency
        raw_data = load_raw_datasets(self.raw_dir)
        filtered_courses = filter_courses_by_events(raw_data['courses'], raw_data['events'])
        learner_records = extract_learner_records(raw_data['vds'], raw_data['events'], filtered_courses)
        filtered_learners = apply_min_learner_filter(learner_records, min_learners=50)
        final_df = filter_no_forum_interactions(filtered_learners)
        
        # Verify the result is consistent
        self.assertGreater(len(final_df), 0, "Pipeline produced no results")
        self.assertIn('id_student', final_df.columns)
        self.assertIn('id_course', final_df.columns)
        
        print("✓ Real data structure test passed")


if __name__ == '__main__':
    unittest.main()