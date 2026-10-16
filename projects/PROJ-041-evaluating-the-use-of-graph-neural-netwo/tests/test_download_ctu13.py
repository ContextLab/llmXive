"""
Unit test for the CTU‑13 download script (Task T002).

The test invokes the script's ``main`` function and
verifies that:
  * The CSV file is created under ``data/raw``.
  * A corresponding ``*.sha256`` side‑car file exists.
  * ``config.yaml`` contains the ``active_dataset: ctu13`` entry.
"""

import os
import yaml

from llmxive_toolkit import paths
from code.data.download_ctu13 import main


def test_download_ctu13():
    # Ensure a clean start – remove any existing artifacts.
    csv_path = paths.data("raw", "ctu13_scenario1.csv")
    sha_path = f"{csv_path}.sha256"
    for p in (csv_path, sha_path):
        if os.path.exists(p):
            os.remove(p)

    # Run the download logic.
    main()

    # Verify CSV exists.
    assert os.path.isfile(csv_path), "CSV file was not created"

    # Verify checksum side‑car exists and is non‑empty.
    assert os.path.isfile(sha_path), "Checksum file missing"
    with open(sha_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert len(content.split()) == 2, "Checksum file malformed"

    # Verify config.yaml was updated.
    config_path = paths.code("config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("active_dataset") == "ctu13", "Config not updated"