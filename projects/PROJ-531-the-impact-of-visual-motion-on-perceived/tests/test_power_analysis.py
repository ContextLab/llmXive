import json
from pathlib import Path

def test_power_analysis_creates_config(tmp_path, monkeypatch):
    """
    Integration test for the power analysis script.
    It runs the script against the existing analysis_ready.csv and checks
    that the expected JSON fields are present and correctly typed.
    """
    # Ensure the script sees the repository root as the working directory
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)

    # Import and run the main function
    from code.power_analysis import main

    exit_code = main()
    assert exit_code == 0, "Script should exit with code 0"

    config_path = Path("data/processed/modeling_config.json")
    assert config_path.exists(), "modeling_config.json must be created"

    with config_path.open() as f:
        cfg = json.load(f)

    # Required keys and types
    required_keys = {
        "effective_n": int,
        "detectable_f2": float,
        "power": float,
        "sc001_pass": bool,
        "power_pass": bool,
        "abort_flag": bool,
    }

    for key, typ in required_keys.items():
        assert key in cfg, f"Missing key {key} in config"
        assert isinstance(cfg[key], typ), f"{key} should be of type {typ.__name__}"