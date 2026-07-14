"""Simple test that the power‑analysis step writes to the log."""

import yaml
from pathlib import Path

from code_02_clean_data import data_cleaning_pipeline  # type: ignore


def test_power_analysis_section(tmp_path, monkeypatch):
    # Prepare a tiny synthetic CSV (real data not required for the logic)
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / "survey_data.csv"
    csv_path.write_text(
        "age,education,farm_size,credit,adoption_binary,membership,extension_contact,collective_action,knowledge_exchange\\n"
        "30,12,1.5,200,1,1,0,1,0\\n"
        "45,8,2.0,150,0,0,1,0,1\\n"
    )

    # Point the config to the temporary directory
    monkeypatch.setenv("PROJECT_CONFIG", str(tmp_path / "code" / "config.yaml"))
    # Ensure the default config file exists (can be empty)
    (tmp_path / "code").mkdir(parents=True, exist_ok=True)
    (tmp_path / "code" / "config.yaml").write_text("{}")

    # Run the pipeline
    data_cleaning_pipeline(input_path=csv_path, output_path=tmp_path / "data" / "processed" / "cleaned_data.csv")

    # Verify that the modeling log now contains the power_analysis section
    log_path = Path("modeling_log.yaml")
    assert log_path.is_file()
    with log_path.open() as f:
        log_content = yaml.safe_load(f)
    assert "power_analysis" in log_content
    assert isinstance(log_content["power_analysis"]["ratio"], float)