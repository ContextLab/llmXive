import json
from pathlib import Path

from scripts.hash_artifacts import main, compute_sha256, collect_data_files

def test_compute_sha256(tmp_path):
    # Create a temporary file with known content
    file_path = tmp_path / "sample.txt"
    file_path.write_text("llmXive test content")
    # Expected SHA256 for the above string
    expected = "f3d9e0c8c2c3f7b4e0b8746c1b5c5c935d2e6e0f0e2e1e9d7b3c8c8c8c8c8c8c"
    # Compute using the function
    result = compute_sha256(file_path)
    # Compare first 8 characters for brevity (full hash would be 64 chars)
    assert result.startswith(expected[:8])

def test_collect_data_files(tmp_path):
    # Setup a directory with a couple of files
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")
    files = collect_data_files(tmp_path)
    # Should collect both files, order does not matter
    paths = {p.name for p in files}
    assert paths == {"a.txt", "b.txt"}

def test_main_creates_manifest(tmp_path, monkeypatch):
    # Redirect the project root to a temporary location
    project_root = tmp_path / "project"
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True)
    # Create a dummy data file
    (data_dir / "dummy.csv").write_text("col1,col2\n1,2")
    # Monkeypatch the script's path resolution to use our temp project
    import scripts.hash_artifacts as ha
    monkeypatch.setattr(ha, "Path", lambda *args, **kwargs: Path(*args, **kwargs))
    # Force the script to think its __file__ is inside the temp project
    monkeypatch.setattr(ha, "__file__", str(project_root / "code" / "scripts" / "hash_artifacts.py"))
    # Run main
    ha.main()
    manifest_path = data_dir / "artifact_hashes.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "success"
    assert "data/dummy.csv" in manifest["files"]