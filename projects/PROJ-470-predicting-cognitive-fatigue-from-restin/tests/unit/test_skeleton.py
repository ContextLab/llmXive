import os
import sys
import unittest
from pathlib import Path

class TestSkeletonFiles(unittest.TestCase):
    def test_skeleton_files_exist(self):
        """
        Test that all required skeleton files exist.
        """
        project_root = Path(__file__).parent.parent.parent
        required_files = [
            "code/config.yaml",
            "code/download.py",
            "code/preprocess.py",
            "code/features.py",
            "code/analysis.py",
            "code/report.py",
            "code/models/__init__.py",
            "docs/README.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.fail(f"Missing skeleton files: {missing_files}")
        
        print("All skeleton files exist.")

if __name__ == '__main__':
    unittest.main()