import json
import pathlib

from code.data_gap_resolver import DataGapResolver, DatasetStatus
from code.config import Config

def test_manifest_created_and_has_minimum_entries(tmp_path, monkeypatch):
    """
    Ensure that ``DataGapResolver.resolve_all_gaps`` creates a manifest
    JSON file and that it contains at least three entries with status
    ``Available`` when the underlying raw files already exist.
    The test runs in a temporary directory to avoid touching the real
    project data.
    """
    # -----------------------------------------------------------------
    # Set up a temporary Config that points to a fresh ``data/raw`` folder
    # -----------------------------------------------------------------
    cfg = Config()
    cfg.data_raw = tmp_path / "raw"
    cfg.results_dir = tmp_path / "results"
    cfg.data_raw.mkdir(parents=True, exist_ok=True)
    cfg.results_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Pretend that three accession files already exist (empty files are fine
    # because the resolver only checks for existence before attempting a
    # download).  The resolver will compute a checksum on these files.
    # -----------------------------------------------------------------
    for acc in cfg.accessions:
        (cfg.data_raw / f"{acc}_dummy_counts.txt").write_text("gene1\tgene2\n1\t2\n")

    resolver = DataGapResolver(cfg)
    report = resolver.resolve_all_gaps()

    manifest_path = pathlib.Path("data") / "manifest.json"
    assert manifest_path.is_file(), "manifest.json was not created"

    with manifest_path.open() as f:
        manifest = json.load(f)

    # All three accessions should be present
    assert len(manifest) == len(cfg.accessions)

    # All should be marked as Available because the dummy files exist
    available = [e for e in manifest if e["status"] == DatasetStatus.AVAILABLE]
    assert len(available) == len(cfg.accessions), "Not all datasets marked Available"

    # The report should reflect the same counts
    assert report["summary"]["available"] == len(cfg.accessions)
    assert report["summary"]["unavailable"] == 0