"""
Unit tests for the Assignment Generator module.
Tests Latin-square design logic and cohort assignment generation.
"""
import unittest
import json
import os
import tempfile
from pathlib import Path
from utils.assignment_generator import (
    generate_latin_square,
    assign_conditions,
    generate_cohort_assignments,
    save_assignments,
    CONDITIONS,
    CONDITION_BASELINE,
    CONDITION_LLM,
    CONDITION_RULE
)

class TestLatinSquare(unittest.TestCase):
    def test_latin_square_size(self):
        """Test that the generated square has correct dimensions."""
        square = generate_latin_square(3)
        self.assertEqual(len(square), 3)
        for row in square:
            self.assertEqual(len(row), 3)

    def test_latin_square_unique_conditions(self):
        """Test that each row and column contains unique conditions."""
        square = generate_latin_square(3)
        
        # Check rows
        for row in square:
            self.assertEqual(len(set(row)), 3)
        
        # Check columns
        for col_idx in range(3):
            column = [square[row_idx][col_idx] for row_idx in range(3)]
            self.assertEqual(len(set(column)), 3)

    def test_latin_square_all_conditions_present(self):
        """Test that all conditions are present in the square."""
        square = generate_latin_square(3)
        all_conditions = set()
        for row in square:
            all_conditions.update(row)
        
        self.assertEqual(all_conditions, set(CONDITIONS))

class TestAssignConditions(unittest.TestCase):
    def test_assign_conditions_valid(self):
        """Test assignment with valid number of tasks."""
        participant_id = "P001"
        task_ids = ["TASK_001", "TASK_002", "TASK_003"]
        
        result = assign_conditions(participant_id, task_ids)
        
        self.assertIn(participant_id, result)
        self.assertEqual(len(result[participant_id]), 3)
        
        # Check that all conditions are assigned
        assigned_conditions = set(result[participant_id].values())
        self.assertEqual(assigned_conditions, set(CONDITIONS))

    def test_assign_conditions_deterministic(self):
        """Test that the same participant gets the same assignment."""
        participant_id = "P005"
        task_ids = ["TASK_001", "TASK_002", "TASK_003"]
        
        result1 = assign_conditions(participant_id, task_ids)
        result2 = assign_conditions(participant_id, task_ids)
        
        self.assertEqual(result1, result2)

    def test_assign_conditions_exceeds_tasks(self):
        """Test error when tasks exceed conditions."""
        participant_id = "P001"
        task_ids = ["TASK_001", "TASK_002", "TASK_003", "TASK_004"]
        
        with self.assertRaises(ValueError):
            assign_conditions(participant_id, task_ids)

class TestCohortAssignments(unittest.TestCase):
    def test_generate_cohort_assignments_count(self):
        """Test that the correct number of assignments are generated."""
        participant_ids = ["P001", "P002", "P003"]
        task_ids = ["TASK_001", "TASK_002", "TASK_003"]
        
        assignments = generate_cohort_assignments(participant_ids, task_ids)
        
        expected_count = len(participant_ids) * len(task_ids)
        self.assertEqual(len(assignments), expected_count)

    def test_generate_cohort_assignments_structure(self):
        """Test the structure of assignment records."""
        participant_ids = ["P001"]
        task_ids = ["TASK_001", "TASK_002", "TASK_003"]
        
        assignments = generate_cohort_assignments(participant_ids, task_ids)
        
        for assignment in assignments:
            self.assertIn("participant_id", assignment)
            self.assertIn("task_id", assignment)
            self.assertIn("condition", assignment)
            self.assertIn(assignment["condition"], CONDITIONS)

    def test_generate_cohort_assignments_balanced(self):
        """Test that conditions are balanced across the cohort."""
        participant_ids = [f"P{i:03d}" for i in range(1, 31)]  # 30 participants
        task_ids = ["TASK_001", "TASK_002", "TASK_003"]
        
        assignments = generate_cohort_assignments(participant_ids, task_ids)
        
        # Count occurrences of each condition
        condition_counts = {cond: 0 for cond in CONDITIONS}
        for assignment in assignments:
            condition_counts[assignment["condition"]] += 1
        
        # With 30 participants and 3 conditions, each condition should appear 30 times
        # (once per participant, distributed across tasks)
        for count in condition_counts.values():
            self.assertEqual(count, 30)

class TestSaveAssignments(unittest.TestCase):
    def test_save_assignments_file_creation(self):
        """Test that assignments are saved to a file."""
        assignments = [
            {"participant_id": "P001", "task_id": "TASK_001", "condition": "baseline"},
            {"participant_id": "P001", "task_id": "TASK_002", "condition": "llm"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_assignments.json")
            save_assignments(assignments, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded, assignments)

    def test_save_assignments_hash_return(self):
        """Test that save_assignments returns a hash."""
        assignments = [
            {"participant_id": "P001", "task_id": "TASK_001", "condition": "baseline"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_assignments.json")
            file_hash = save_assignments(assignments, output_path)
            
            self.assertIsInstance(file_hash, str)
            self.assertEqual(len(file_hash), 64)  # SHA-256 hex length

if __name__ == "__main__":
    unittest.main()