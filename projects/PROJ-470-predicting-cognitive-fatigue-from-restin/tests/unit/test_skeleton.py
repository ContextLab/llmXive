"""Test T002: Verify code skeleton files exist."""
import os
import sys
import unittest

# Define the expected skeleton files relative to project root
EXPECTED_FILES = [
    "code/config.yaml",
    "code/download.py",
    "code/preprocess.py",
    "code/features.py",
    "code/analysis.py",
    "code/report.py",
    "code/models/__init__.py",
]

class TestCodeSkeleton(unittest.TestCase):
    def test_all_skeleton_files_exist(self):
        """Assert that all listed files in code/ exist."""
        missing = []
        for rel_path in EXPECTED_FILES:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", rel_path)
            if not os.path.isfile(full_path):
                missing.append(rel_path)
        
        self.assertEqual(
            len(missing), 0,
            f"Missing code skeleton files: {', '.join(missing)}"
        )

if __name__ == "__main__":
    unittest.main()
