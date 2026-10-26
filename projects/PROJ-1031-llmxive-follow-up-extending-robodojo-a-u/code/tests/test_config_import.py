"""
Integration test for the top‑level configuration module.

The test simply imports `code.config` and checks that:
  * The deterministic random seed is set to the expected value (42).
  * Exactly 18 real‑world RoboDojo task identifiers are loaded.
The import triggers the lazy loading logic in `code/config.py`, which
streams the first 18 task IDs from the public RoboDojo dataset.
"""
import sys
import pytest

# Ensure the project root is on the import path so that `import code.config`
# resolves to the package we just created.
import pathlib
project_root = pathlib.Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_config_import_and_task_ids():
    import code.config as cfg

    # Verify deterministic seed.
    assert hasattr(cfg, "SEED"), "SEED constant missing"
    assert cfg.SEED == 42, f"Expected SEED == 42, got {cfg.SEED}"

    # Verify that exactly 18 task IDs were fetched.
    assert hasattr(cfg, "TASK_IDS"), "TASK_IDS constant missing"
    assert isinstance(cfg.TASK_IDS, list), "TASK_IDS should be a list"
    assert len(cfg.TASK_IDS) == 18, f"Expected 18 task IDs, got {len(cfg.TASK_IDS)}"
    # All IDs should be non‑empty strings.
    for tid in cfg.TASK_IDS:
        assert isinstance(tid, str) and tid, f"Invalid task ID encountered: {tid}"