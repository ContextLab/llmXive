"""Validate that the quickstart run‑book produced all declared outputs."""
import subprocess
from pathlib import Path

def run_script(cmd: list[str]) -> None:
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {result.stderr}")

def validate_outputs() -> None:
    expected = [
        "data/raw/survey_data.csv",
        "data/processed/cleaned_data.csv",
        "data/processed/engineered_data.csv",
        "results/validity_metrics.yaml",
        "results/report.pdf",
        "modeling_log.yaml",
    ]
    missing = [p for p in expected if not Path(p).is_file()]
    if missing:
        raise AssertionError(f"Missing expected outputs: {', '.join(missing)}")
    print("All expected outputs are present.")

def main() -> None:
    # Run the pipeline as defined in quickstart.md
    run_script(["python", "code/01_download_data.py", "--synthetic"])
    run_script(["python", "code/02_clean_data.py"])
    run_script(["python", "code/03_engineer_features.py"])
    run_script(["python", "code/04_model_analysis.py"])
    run_script(["python", "code/05_generate_report.py"])
    validate_outputs()

if __name__ == "__main__":
    main()