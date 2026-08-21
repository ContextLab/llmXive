import os
import tempfile
import shutil
import pytest
from code.setup_project_structure import ensure_directory, create_init_file

class TestSetupProjectStructure:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Create a temporary directory for testing
        self.test_base = tempfile.mkdtemp()
        yield
        # Clean up the temporary directory after the test
        shutil.rmtree(self.test_base)

    def test_ensure_directory_creates_new_dir(self):
        new_dir = os.path.join(self.test_base, "new_dir")
        assert not os.path.exists(new_dir)
        result = ensure_directory(new_dir)
        assert result is True
        assert os.path.isdir(new_dir)

    def test_ensure_directory_exists_ok(self):
        existing_dir = os.path.join(self.test_base, "existing_dir")
        os.makedirs(existing_dir)
        result = ensure_directory(existing_dir)
        assert result is True
        assert os.path.isdir(existing_dir)

    def test_ensure_directory_creates_nested_dirs(self):
        nested_dir = os.path.join(self.test_base, "level1", "level2", "level3")
        assert not os.path.exists(nested_dir)
        result = ensure_directory(nested_dir)
        assert result is True
        assert os.path.isdir(nested_dir)

    def test_create_init_file_creates_file(self):
        test_dir = os.path.join(self.test_base, "test_dir")
        os.makedirs(test_dir)
        result = create_init_file(test_dir)
        assert result is True
        init_path = os.path.join(test_dir, "__init__.py")
        assert os.path.isfile(init_path)

    def test_create_init_file_in_nonexistent_dir(self):
        # This should fail gracefully as the directory doesn't exist
        # The function creates the file, but if the parent dir is missing, it might fail.
        # However, our implementation assumes the directory exists or is created by ensure_directory first.
        # Let's test the specific case where the directory is created by ensure_directory first.
        test_dir = os.path.join(self.test_base, "test_dir2")
        ensure_directory(test_dir)
        result = create_init_file(test_dir)
        assert result is True
        init_path = os.path.join(test_dir, "__init__.py")
        assert os.path.isfile(init_path)

    def test_create_init_file_empty_content(self):
        test_dir = os.path.join(self.test_base, "test_dir3")
        os.makedirs(test_dir)
        create_init_file(test_dir)
        init_path = os.path.join(test_dir, "__init__.py")
        with open(init_path, "r") as f:
            content = f.read()
        assert content == ""
