"""T004 verification: run setup_logging() and confirm a log file is
created under artifacts/logs/, and that code.models exposes the two
data-model classes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import setup_logging, get_config, PROJECT_ROOT
import models


def main() -> int:
    logger = setup_logging()
    logger.info("T004 verification: logging initialised")

    log_path = PROJECT_ROOT / get_config()["LOG_PATH"]
    assert log_path.exists(), f"log file was not created: {log_path}"
    assert log_path.parent == PROJECT_ROOT / "artifacts" / "logs", (
        f"log file not under artifacts/logs/: {log_path}"
    )
    print(f"OK: log file created at {log_path}")

    assert hasattr(models, "RootPhenotypeRecord")
    assert hasattr(models, "SoilNutrientRecord")
    rec = models.RootPhenotypeRecord(species="Zea mays", root_length=12.5)
    soil = models.SoilNutrientRecord(phosphorus=3.2, nitrogen=1.1)
    assert rec.is_valid_for_analysis()
    assert soil.is_complete_for_analysis()
    print("OK: models.RootPhenotypeRecord and models.SoilNutrientRecord import cleanly")

    template = PROJECT_ROOT / "config.yaml.template"
    assert template.exists(), f"missing template: {template}"
    print(f"OK: {template} exists")

    # The config loader must expose every key pipeline scripts request
    cfg = get_config()
    for key in [
        "DATA_PATH",
        "PROCESSED_PATH",
        "ARTIFACTS_PATH",
        "LOGS_PATH",
        "LOG_PATH",
        "LOG_LEVEL",
        "SEED",
    ]:
        assert key in cfg, f"get_config() missing key: {key}"
    print("OK: get_config() provides all standard keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
