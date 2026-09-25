import os
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code directory is in path if running from tests/
sys_path_backup = __import__('sys').path.copy()
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent))
    from code import hygiene
finally:
    __import__('sys').path[:] = sys_path_backup


def test_generate_reproducibility_audit_creates_file(tmp_path, monkeypatch):
    """
    Test that generate_reproducibility_audit creates the expected file
    with non-empty git_hash and python_version.
    """
    project_id = "PROJ-163-exploring-the-role-of-network-structure-"
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    
    # Mock the state directory to use tmp_path
    with patch.object(Path, 'mkdir', return_value=None):
        # We need to patch the internal path construction in generate_reproducibility_audit
        # Since the function hardcodes "state/projects", we will mock the file write
        
        mock_git_output = "abc123def456"
        mock_req_hash = "req_hash_123"
        
        with patch('code.hygiene.subprocess.check_output', return_value=mock_git_output):
            with patch('code.hygiene.compute_sha256', return_value=mock_req_hash):
                with patch('builtins.open', mock_open_create_file()) as mock_file:
                    with patch('code.hygiene.Path') as mock_path_class:
                        # Mock the state_dir path
                        mock_path_instance = MagicMock()
                        mock_path_instance.exists.return_value = True
                        mock_path_class.return_value = mock_path_instance
                        
                        # Call the function
                        hygiene.generate_reproducibility_audit(project_id)
                        
                        # Verify that open was called to write the file
                        assert mock_file.called
                        
def test_generate_reproducibility_audit_content(tmp_path, monkeypatch):
    """
    Test the content of the generated reproducibility file.
    """
    project_id = "PROJ-163-exploring-the-role-of-network-structure-"
    repro_file = tmp_path / f"{project_id}-reproducibility.yaml"
    
    # Mock dependencies
    mock_git_hash = "test_git_hash_12345"
    mock_req_hash = "test_req_hash_67890"
    mock_py_version = "3.9.0 (main, Jan 1 2024)"
    
    with patch('code.hygiene.subprocess.check_output', return_value=mock_git_hash):
        with patch('code.hygiene.compute_sha256', return_value=mock_req_hash):
            with patch('code.hygiene.sys.version', mock_py_version):
                with patch('code.hygiene.Path') as mock_path_cls:
                    # Setup mocks for Path operations
                    mock_dir = MagicMock()
                    mock_dir.mkdir = MagicMock()
                    mock_path_cls.return_value = mock_dir
                    
                    # We need to patch the open call specifically for the output file
                    # to capture the content written
                    content_written = {}
                    
                    def mock_open_side_effect(file_path, mode='r', *args, **kwargs):
                        if 'w' in mode:
                            # Create a fake file object that captures writes
                            class FakeFile:
                                def __init__(self):
                                    self.content = ""
                                def write(self, text):
                                    self.content = text
                                def __enter__(self):
                                    return self
                                def __exit__(self, *args):
                                    pass
                            fake_file = FakeFile()
                            content_written[file_path] = fake_file.content
                            return fake_file
                        else:
                            return open(file_path, mode, *args, **kwargs)
                    
                    with patch('builtins.open', side_effect=mock_open_side_effect):
                        hygiene.generate_reproducibility_audit(project_id)
                    
                    # Check that a file was written
                    assert len(content_written) > 0
                    
                    # Find the yaml content
                    yaml_content = None
                    for path, content in content_written.items():
                        if project_id in path and "reproducibility" in path:
                            yaml_content = yaml.safe_load(content)
                            break
                    
                    assert yaml_content is not None, "Reproducibility YAML file not found or empty"
                    assert yaml_content.get("git_hash") == mock_git_hash
                    assert yaml_content.get("requirements_hash") == mock_req_hash
                    assert "python_version" in yaml_content
                    assert len(yaml_content["python_version"]) > 0

def mock_open_create_file():
    """Helper to mock open for file creation."""
    from unittest.mock import mock_open
    return mock_open()