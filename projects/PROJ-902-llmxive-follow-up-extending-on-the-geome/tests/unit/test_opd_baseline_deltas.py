"""
Unit test for verifying that the OPD baseline script outputs per‑layer weight
deltas.

The baseline script (`src/train/opd_baseline.py`) is expected to write the
weight‑delta tensors for each layer into ``data/baseline_deltas/`` as ``.pt``
files.  This test runs the script in an isolated temporary directory and
checks that at least one such file is produced and that it can be loaded as a
``torch.Tensor``.
"""

import pathlib
import torch

# Import the entry‑point of the baseline script.
from src.train.opd_baseline import main

def test_opd_baseline_outputs_weight_deltas(tmp_path, monkeypatch):
    """
    Run the baseline script and assert that per‑layer weight‑delta files are
    created.

    The test changes the working directory to a temporary location so that the
    script writes its output under ``tmp_path/data/baseline_deltas/`` instead of
    the repository’s real ``data/`` folder.  This guarantees isolation and
    automatic cleanup after the test run.
    """
    # Switch the current working directory to the temporary directory.
    monkeypatch.chdir(tmp_path)

    # Run the baseline training script.  It should complete without raising an
    # exception and write delta files to ``data/baseline_deltas/``.
    main()

    # Construct the expected output directory.
    baseline_dir = pathlib.Path("data") / "baseline_deltas"

    # Verify the directory exists.
    assert baseline_dir.is_dir(), f"Expected directory {baseline_dir} does not exist."

    # Look for any ``.pt`` files – each should contain a torch tensor.
    delta_files = list(baseline_dir.glob("*.pt"))
    assert delta_files, f"No weight‑delta ``.pt`` files found in {baseline_dir}."

    # Load the first file to ensure it is a valid torch tensor.
    sample_tensor = torch.load(delta_files[0])
    assert isinstance(
        sample_tensor, torch.Tensor
    ), f"The file {delta_files[0]} does not contain a torch.Tensor."

    # (Optional) sanity‑check that the tensor is not empty.
    assert sample_tensor.numel() > 0, "Loaded weight delta tensor is empty."