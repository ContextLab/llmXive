import os
import sys
import tempfile
import shutil
import pytest

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.setup_project_structure import ensure_directory, create_init_file

class TestProjectStructure:
    @pytest.fixture
    def temp_base(self):
        """Create a temporary base directory for testing."""
        base = tempfile.mkdtemp()
        yield base
        shutil.rmtree(base)

    def test_ensure_directory_creates_new(self, temp_base):
        new_dir = os.path.join(temp_base, "new_folder")
        assert not os.path.exists(new_dir)
        result = ensure_directory(new_dir)
        assert result is True
        assert os.path.isdir(new_dir)

    def test_ensure_directory_exists_noop(self, temp_base):
        existing = os.path.join(temp_base, "existing")
        os.makedirs(existing)
        result = ensure_directory(existing)
        assert result is True
        assert os.path.isdir(existing)

    def test_create_init_file(self, temp_base):
        target_dir = os.path.join(temp_base, "target")
        ensure_directory(target_dir)
        result = create_init_file(target_dir)
        assert result is True
        init_path = os.path.join(target_dir, "__init__.py")
        assert os.path.isfile(init_path)
        with open(init_path, "r") as f:
            content = f.read()
            assert "Auto-generated" in content

    def test_full_pipeline_simulation(self, temp_base):
        """Simulate the T001a/b/c logic on a temp base."""
        # T001a
        core_dirs = ["code", "data", "results", "tests", "docs"]
        for d in core_dirs:
            ensure_directory(os.path.join(temp_base, d))
        
        # T001b
        ensure_directory(os.path.join(temp_base, "state"))

        # T001c
        init_dirs = [
            os.path.join(temp_base, "code"),
            os.path.join(temp_base, "tests"),
            os.path.join(temp_base, "tests", "unit"),
            os.path.join(temp_base, "tests", "integration")
        ]
        for d in init_dirs:
            ensure_directory(d)
            create_init_file(d)

        # Verification
        assert os.path.isdir(os.path.join(temp_base, "code"))
        assert os.path.isdir(os.path.join(temp_base, "state"))
        assert os.path.isfile(os.path.join(temp_base, "tests", "__init__.py"))
        assert os.path.isfile(os.path.join(temp_base, "tests", "unit", "__init__.py"))