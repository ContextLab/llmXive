import os
import unittest

class TestSkeletonFiles(unittest.TestCase):
    """Test that all required code skeleton files exist."""

    def test_all_skeleton_files_exist(self):
        """Assert that all listed files in code/ exist."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        code_dir = os.path.join(base_dir, "code")

        required_files = [
            "config.yaml",
            "download.py",
            "preprocess.py",
            "features.py",
            "analysis.py",
            "report.py",
            os.path.join("models", "__init__.py"),
        ]

        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(code_dir, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)

        self.assertEqual(
            len(missing_files),
            0,
            f"Missing skeleton files: {', '.join(missing_files)}",
        )

if __name__ == "__main__":
    unittest.main()