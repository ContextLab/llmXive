"""
Verify that the CLI aborts gracefully when no species are configured.
"""

import pytest

def test_cli_handles_empty_species_list(monkeypatch, tmp_path):
    # Mock config to return an empty species list
    class DummyConfig:
        data_root = tmp_path
        output_path = tmp_path / "data" / "processed"
        phylogeny_path = tmp_path / "data" / "raw" / "phylogeny" / "tree.newick"

    def dummy_load_config(*args, **kwargs):
        return DummyConfig()

    monkeypatch.setattr("code.config.load_config", dummy_load_config)

    # Patch get_species_list to return empty list
    monkeypatch.setattr("code.config.get_species_list", lambda: [])

    # Run CLI with download_and_align step
    from code.cli.main import main
    import sys
    test_args = ["prog", "--step", "download_and_align"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Expect no exception; the function should log a warning and exit
    main()
    # No aligned matrix should be created
    aligned_path = tmp_path / "data" / "processed" / "aligned_matrix.csv"
    assert not aligned_path.is_file()
