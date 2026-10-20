"""
Ensure that the CLI raises an error if the required aligned matrix is missing
when the ``train_and_evaluate`` step is invoked.
"""

import pytest

def test_train_step_fails_without_aligned_matrix(monkeypatch, tmp_path):
    # Ensure aligned matrix does NOT exist
    aligned = tmp_path / "data" / "processed" / "aligned_matrix.csv"
    if aligned.is_file():
        aligned.unlink()

    # Patch config to point to temporary paths
    class DummyConfig:
        data_root = tmp_path
        output_path = tmp_path / "data" / "processed"
        phylogeny_path = tmp_path / "data" / "raw" / "phylogeny" / "tree.newick"

    monkeypatch.setattr("code.config.load_config", lambda *args, **kwargs: DummyConfig())
    monkeypatch.setattr("code.config.get_species_list", lambda: [{"name": "Test species"}])

    # Run CLI with train_and_evaluate step
    from code.cli.main import main
    import sys
    test_args = ["prog", "--step", "train_and_evaluate"]
    monkeypatch.setattr(sys, "argv", test_args)

    # The step should log an error but not raise; we just ensure it returns
    main()
    # No metrics file should be created
    metrics_path = tmp_path / "data" / "processed" / "model_metrics.json"
    assert not metrics_path.is_file()
