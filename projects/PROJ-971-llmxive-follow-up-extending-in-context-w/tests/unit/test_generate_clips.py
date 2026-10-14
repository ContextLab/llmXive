"""
Unit test for ``src.pipeline.generate_clips``.
Verifies that the expected number of ``.npz`` files are created and that each
file contains the required arrays.
"""

import pathlib

from llmxive_toolkit import paths

def test_generate_clips_creates_expected_files(tmp_path, monkeypatch):
    """
    Run the generation script with a temporary output directory and assert
    that exactly 50 files are produced and each contains ``states``,
    ``actions`` and ``observations`` arrays.
    """
    # Import the module after monkey‑patching the data path to a temp dir.
    import importlib
    import sys

    # Patch the ``paths.data`` function to point to the temporary directory.
    # The original ``paths`` module resolves to the project root; we replace
    # its ``data`` method with one that returns ``tmp_path / "raw"``.
    from llmxive_toolkit import paths as original_paths

    def fake_data(*parts):
        return tmp_path.joinpath(*parts)

    monkeypatch.setattr(original_paths, "data", fake_data)

    # Reload the target module to pick up the patched paths.
    module_name = "src.pipeline.generate_clips"
    if module_name in sys.modules:
        del sys.modules[module_name]
    generate_module = importlib.import_module(module_name)

    # Run the main function with default arguments (50 clips).
    generate_module.main()

    # Verify file count.
    raw_dir = fake_data("raw")
    npz_files = list(raw_dir.glob("clip_*.npz"))
    assert len(npz_files) == 50, f"Expected 50 clips, found {len(npz_files)}"

    # Verify each .npz contains the required arrays.
    import numpy as np

    for file in npz_files:
        with np.load(file) as data:
            for key in ("states", "actions", "observations"):
                assert key in data, f"{file.name} missing required array '{key}'"
            # Basic sanity checks: non‑empty and matching first dimension.
            states = data["states"]
            actions = data["actions"]
            observations = data["observations"]
            assert states.shape[0] == actions.shape[0] == observations.shape[0]
            assert states.shape[0] > 0, "Clip contains zero timesteps"