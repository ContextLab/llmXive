import json
from pathlib import Path

# Import the script's main function
from define_rss_size import main as define_rss_size_main

def test_define_rss_size_creates_valid_config(tmp_path, monkeypatch):
    """
    Ensure that running define_rss_size.py creates a rss_config.json
    with a positive integer not exceeding 150,000.
    """
    # Redirect the metadata directory to a temporary location
    project_root = Path(__file__).resolve().parents[2]  # project root
    metadata_dir = project_root / "data" / "metadata"

    # Ensure a clean state
    if metadata_dir.exists():
        for p in metadata_dir.iterdir():
            p.unlink()
    else:
        metadata_dir.mkdir(parents=True)

    # Run the script
    define_rss_size_main()

    # Verify the JSON file exists
    config_path = metadata_dir / "rss_config.json"
    assert config_path.is_file(), "rss_config.json was not created"

    # Load and validate contents
    with open(config_path, "r") as f:
        config = json.load(f)

    rss_size = config.get("rss_size")
    assert isinstance(rss_size, int), "rss_size must be an integer"
    assert rss_size > 0, "rss_size must be positive"
    assert rss_size <= 150_000, "rss_size must not exceed 150,000"

    # Ensure the reason field is present and non‑empty
    assert "reason" in config and isinstance(config["reason"], str) and config["reason"], \
        "reason field must be a non‑empty string"