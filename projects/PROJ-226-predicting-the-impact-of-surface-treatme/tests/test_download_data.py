import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

def test_download_data_creates_files(tmp_path, monkeypatch):
    """
    Verify that ``code/download_data.py`` creates the expected raw CSV files,
    the merged CSV, and a correctly formatted checksums file.
    """
    # Ensure a clean environment inside the temporary pytest directory.
    # The repository's data directories are relative to the project root;
    # we point the toolkit's ``paths`` helper to the temporary location.
    monkeypatch.setattr(
        "llmxive_toolkit.paths.root",
        Path(tmp_path),
    )
    # Re‑create the minimal fixture CSV that the script will fall back to.
    source_dir = Path(tmp_path) / "data" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    example_csv = source_dir / "example.csv"
    example_csv.write_text(
        "plasma_power_w,exposure_time_s,chemical_concentration_pct,polymer_surface_energy,substrate_roughness_nm,adhesion_strength_mj_m2,treatment_type,pair_id\\n"
        "150,30,5,42.5,120,1.8,Oxygen Plasma,PP_Al\\n"
    )
    # Create an empty availability report (the script will fall back to the CSV).
    (Path(tmp_path) / "data" / "source" / "availability_report.json").write_text(
        json.dumps({"datasets": []})
    )

    # Run the script.
    from code.download_data import main as download_main
    download_main()

    raw_dir = Path(tmp_path) / "data" / "raw"
    # Expected source files (the script copies the example CSV three times – once per
    # discovered CSV in ``data/source/``; here we only have one CSV, so we expect a
    # single raw file named ``example.csv``).
    expected_raw = raw_dir / "example.csv"
    assert expected_raw.is_file(), "The source CSV should be copied to data/raw/"

    # Merged file must exist and contain the ``source`` column.
    merged = raw_dir / "adhesion_raw.csv"
    assert merged.is_file(), "Merged adhesion_raw.csv should be created"
    df = pd.read_csv(merged)
    assert "source" in df.columns, "Merged CSV must contain a 'source' column"

    # Checksums file must exist and have one line matching the copied file.
    checksums = raw_dir / "checksums.txt"
    assert checksums.is_file(), "checksums.txt should be written"
    lines = checksums.read_text().strip().splitlines()
    assert len(lines) == 1, "Exactly one checksum line expected"
    checksum, filename = lines[0].split("  ")
    assert filename == expected_raw.name, "Checksum line must reference the raw file"
    # Verify that the recorded checksum matches the actual file.
    import hashlib
    h = hashlib.sha256()
    with expected_raw.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    assert h.hexdigest() == checksum, "Recorded checksum must be correct"