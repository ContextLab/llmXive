import os
import unittest
import tempfile
import shutil
import sys

# Add parent directory to path to import setup_project_structure
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_project_structure import ensure_directory, create_init_file

class TestSetupStructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_ensure_directory_creates_dir(self):
        test_path = "test_new_dir"
        result = ensure_directory(test_path)
        self.assertTrue(result)
        self.assertTrue(os.path.isdir(test_path))

    def test_ensure_directory_exists(self):
        test_path = "test_existing_dir"
        os.makedirs(test_path)
        result = ensure_directory(test_path)
        self.assertTrue(result)

    def test_create_init_file(self):
        test_dir = "test_init_dir"
        os.makedirs(test_dir)
        result = create_init_file(test_dir)
        self.assertTrue(result)
        self.assertTrue(os.path.isfile(os.path.join(test_dir, "__init__.py")))

    def test_create_init_file_in_subdir(self):
        test_dir = "parent/child"
        os.makedirs(test_dir, exist_ok=True)
        result = create_init_file(test_dir)
        self.assertTrue(result)
        self.assertTrue(os.path.isfile(os.path.join(test_dir, "__init__.py")))

if __name__ == "__main__":
    unittest.main()
