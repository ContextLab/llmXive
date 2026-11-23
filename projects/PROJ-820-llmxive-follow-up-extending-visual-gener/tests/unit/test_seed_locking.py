import json
import shutil
from pathlib import Path

import pytest

from llmxive_toolkit import paths, get_logger
from generation.seed_manifest import generate_seed_manifest
from generation.diffusion_runner import (
    main as diffusion_main,
    _ensure_seed_manifest,
    _ensure_prompts_and_constraints,
)

logger = get_logger(__name__)

@pytest.fixture(scope="function")
def clean_workspace(tmp_path):
    """
    Set up a temporary workspace that mimics the project data layout.
    The fixture copies the minimal required CSV file into a temporary
    location and points the toolkit paths to that temporary directory.
    """
    # Copy the real scene descriptions CSV into the temp directory
    src_csv = Path("data/raw/scene_descriptions.csv")
    dst_raw = tmp_path / "data" / "raw"
    dst_raw.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_csv, dst_raw / src_csv.name)

    # Monkey‑patch the llmxive_toolkit.paths helpers to resolve under the temp dir
    original_root = paths.root
    paths.root = tmp_path  # type: ignore

    yield tmp_path

    # Restore original root after test
    paths.root = original_root  # type: ignore

def test_seed_manifest_creation(clean_workspace):
    """
    Verify that the seed manifest is generated and contains deterministic seeds
    for each scene.
    """
    manifest_path = paths.data("derived", "seed_manifest.json")
    # Ensure no manifest exists beforehand
    if manifest_path.exists():
        manifest_path.unlink()

    # Generate manifest using the helper
    generate_seed_manifest(
        scene_csv_path=paths.data("raw", "scene_descriptions.csv"),
        manifest_path=manifest_path,
        base_seed=42,
    )

    assert manifest_path.is_file(), "seed_manifest.json was not created"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic structural checks
    assert "base_seed" in data
    assert data["base_seed"] == 42
    assert "seeds" in data
    # At least one scene should be present
    assert len(data["seeds"]) > 0
    # Verify that each entry contains both baseline and experimental seeds
    for scene_id, seeds in data["seeds"].items():
        assert "baseline" in seeds
        assert "experimental" in seeds
        # Seeds should be integers
        assert isinstance(seeds["baseline"], int)
        assert isinstance(seeds["experimental"], int)

def test_full_diffusion_pipeline_execution(clean_workspace):
    """
    End‑to‑end smoke test for the diffusion runner:
    - Ensure the seed manifest exists (generated if missing)
    - Ensure prompts and minimal physics constraints are present
    - Run the diffusion runner main entry point
    - Verify that PNG files, seed_lock_status.json and generation_failure_log.json are written
    """
    # 1. Ensure seed manifest
    manifest_path = _ensure_seed_manifest()
    assert manifest_path.is_file(), "Seed manifest should exist after helper call"

    # 2. Load a small subset of scene IDs (first 5) for a quick run
    csv_path = paths.data("raw", "scene_descriptions.csv")
    import csv as _csv
    scene_ids = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            scene_ids.append(row.get("scene_id") or row.get("id") or next(iter(row)))

    # 3. Ensure prompts and constraints for these scenes
    groups = ["baseline", "experimental"]
    _ensure_prompts_and_constraints(scene_ids, groups)

    # 4. Run the diffusion runner (this will load the LCM‑LoRA model and generate images)
    diffusion_main()

    # 5. Verify generated artifacts
    for scene_id in scene_ids:
        for group in groups:
            img_path = paths.derived("generated_images", group, f"{scene_id}.png")
            assert img_path.is_file(), f"Generated image missing: {img_path}"

    lock_status_path = paths.derived("generated_images").parent / "seed_lock_status.json"
    assert lock_status_path.is_file(), "seed_lock_status.json was not created"

    # Load lock status and check that deviation_ok is True for all entries
    with open(lock_status_path, "r", encoding="utf-8") as f:
        lock_status = json.load(f)

    for scene_id in scene_ids:
        for group in groups:
            entry = lock_status.get(scene_id, {}).get(group, {})
            assert entry.get("mode") in {"exact", "fallback"}
            assert entry.get("deviation_ok") is True, f"Deviation check failed for {scene_id}/{group}"

    # Generation failure log should exist (may be empty)
    failure_log_path = paths.derived("generated_images").parent / "generation_failure_log.json"
    assert failure_log_path.is_file(), "generation_failure_log.json was not created"