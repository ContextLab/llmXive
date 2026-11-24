"""
Integration test for the checksum generation script.

The test runs ``code.validation.generate_checksums.main`` which creates
``data/checksums.sha256``. It then verifies:

1. The manifest file exists.
2. At least five entries refer to files under ``data/raw/`` (the simulated
   dataset contains many such files).
3. Each listed file actually exists and its recorded hash matches a freshly
   computed SHA‑256 digest.
"""

from pathlib import Path

from llmxive_toolkit import paths

import importlib


def test_generate_checksums_and_validate():
    # Import the module freshly to avoid state leakage
    gen_mod = importlib.import_module("code.validation.generate_checksums")

    # Run the script's main function (it writes the manifest)
    exit_code = gen_mod.main()
    assert exit_code == 0, "Checksum script exited with non‑zero status"

    manifest_path = paths.data("checksums.sha256")
    assert manifest_path.is_file(), "Manifest file was not created"

    # Read manifest lines
    lines = manifest_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 5, "Manifest should contain at least five entries"

    raw_prefix = Path("data/raw").as_posix()
    raw_entries = [line for line in lines if line.split("  ", 1)[1].startswith(raw_prefix)]
    assert len(raw_entries) >= 5, "At least five simulated raw files should be listed"

    # Verify each entry's hash matches the actual file content
    for line in raw_entries:
        expected_hash, rel_path = line.split("  ", 1)
        file_path = Path(paths.root) / rel_path
        assert file_path.is_file(), f"Manifest references missing file {rel_path}"
        
        # Compute hash independently
        hasher = __import__("hashlib").sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"