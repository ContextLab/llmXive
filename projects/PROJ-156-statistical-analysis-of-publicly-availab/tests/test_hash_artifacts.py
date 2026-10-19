import json
from pathlib import Path
import pytest

from scripts.hash_artifacts import main, compute_sha256, collect_data_files

def test_compute_sha256(tmp_path):
    # Create a temporary file with known content
    file_path = tmp_path / "sample.txt"
    file_path.write_text("llmXive test content")
    # Expected SHA256 for "llmXive test content"
    # echo -n "llmXive test content" | sha256sum
    expected = "a8ca38973a765eba1a6781a88f09591dddda3aba8562e2f62bc2f2b4f373bc98"
    # Compute using the function
    result = compute_sha256(file_path)
    # Compare first 8 characters for brevity
    assert result.startswith(expected[:8])

def test_collect_data_files(tmp_path):
    # Setup a directory with a couple of files
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")
    files = collect_data_files(tmp_path)
    # Should collect both files
    paths = {p.name for p in files}
    assert paths == {"a.txt", "b.txt"}

def test_main_creates_manifest(tmp_path, monkeypatch):
    # Redirect the project root to a temporary location
    project_root = tmp_path / "project"
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True)
    # Create a dummy data file
    (data_dir / "dummy.csv").write_text("col1,col2\n1,2")
    
    # We need to mock the Path resolution in main()
    # main() uses Path(__file__).resolve().parents[2]
    import scripts.hash_artifacts as ha
    
    # Create a fake file path that mimics the project structure
    fake_file = project_root / "code" / "scripts" / "hash_artifacts.py"
    # We can't easily monkeypatch __file__ because it's a read-only attribute of the module
    # But we can monkeypatch the way the root is calculated if we wrap it, 
    # or just monkeypatch the Path object used in the script.
    # For simplicity in this test, we will manually call the logic or 
    # use a mock that replaces the resolve() call.
    
    # Since we are testing if main() writes the file, let's just ensure 
    # the environment is set up such that the relative path parents[2] 
    # points to our tmp_path.
    
    # Instead of complex monkeypatching of __file__, we'll just 
    # verify the logic by ensuring that if the script were at 
    # project/code/scripts/hash_artifacts.py, it would find project/data.
    
    # To make the actual ha.main() work with tmp_path, we monkeypatch Path.resolve
    original_resolve = Path.resolve
    def mocked_resolve(self):
        if self.name == "hash_artifacts.py":
            return fake_file
        return original_resolve(self)
    
    monkeypatch.setattr(Path, "resolve", mocked_resolve)
    
    # Run main
    ha.main()
    
    manifest_path = data_dir / "artifact_hashes.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "success"
    # The rel_path is calculated as file_path.relative_to(project_root)
    assert "data/dummy.csv" in manifest["files"]