"""Unit tests for configuration files."""

import pathlib
import yaml


def _load_yaml(relative_path: pathlib.Path) -> dict:
    """Load a YAML file relative to the repository root."""
    root = pathlib.Path(__file__).resolve().parents[2]  # tests/unit/ -> tests/ -> repo root
    full_path = root / relative_path
    assert full_path.is_file(), f"Missing file: {full_path}"
    with full_path.open("r") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"YAML content must be a mapping in {full_path}"
    return data


def test_species_config():
    """Validate that species.yaml contains the required structure."""
    species_cfg = _load_yaml(pathlib.Path("code/src/config/species.yaml"))

    # At least one species must be defined
    assert species_cfg, "species.yaml must define at least one species"

    for species, cfg in species_cfg.items():
        # Each species entry must be a mapping
        assert isinstance(cfg, dict), f"Entry for {species} must be a mapping"

        # Required keys
        required_keys = {"accessions", "held_out_series", "min_samples"}
        missing = required_keys - cfg.keys()
        assert not missing, f"Species '{species}' missing keys: {missing}"

        # accessions must be a non‑empty list of strings
        accessions = cfg["accessions"]
        assert isinstance(accessions, list) and accessions, (
            f"'accessions' for {species} must be a non‑empty list"
        )
        for acc in accessions:
            assert isinstance(acc, str) and acc, f"Invalid accession '{acc}' in {species}"

        # held_out_series must be a string present in accessions
        held_out = cfg["held_out_series"]
        assert isinstance(held_out, str) and held_out, (
            f"'held_out_series' for {species} must be a non‑empty string"
        )
        assert held_out in accessions, (
            f"'held_out_series' ({held_out}) not listed in 'accessions' for {species}"
        )

        # min_samples must be an integer >= 50
        min_samples = cfg["min_samples"]
        assert isinstance(min_samples, int) and min_samples >= 50, (
            f"'min_samples' for {species} must be an integer >= 50"
        )


def test_parameters_config():
    """Validate that parameters.yaml contains sensible defaults."""
    params_cfg = _load_yaml(pathlib.Path("code/src/config/parameters.yaml"))

    # Required keys
    required_keys = {"threshold", "norm_method", "seed"}
    missing = required_keys - params_cfg.keys()
    assert not missing, f"parameters.yaml missing keys: {missing}"

    # threshold must be a float >= 0.75
    threshold = params_cfg["threshold"]
    assert isinstance(threshold, (float, int)), "'threshold' must be numeric"
    assert threshold >= 0.75, f"'threshold' must be >= 0.75 (found {threshold})"

    # norm_method must be either 'vst' or 'tpm'
    norm_method = params_cfg["norm_method"]
    assert isinstance(norm_method, str), "'norm_method' must be a string"
    assert norm_method in {"vst", "tpm"}, (
        f"'norm_method' must be 'vst' or 'tpm' (found '{norm_method}')"
    )

    # seed must be an integer
    seed = params_cfg["seed"]
    assert isinstance(seed, int), f"'seed' must be an integer (found {seed})"


if __name__ == "__main__":
    # When run directly, execute the tests (useful for quick debugging)
    test_species_config()
    test_parameters_config()
    print("All configuration tests passed.")