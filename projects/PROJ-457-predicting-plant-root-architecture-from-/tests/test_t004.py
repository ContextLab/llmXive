import pytest
from pathlib import Path
from code.config import setup_logging, get_config
from code.models import RootPhenotypeRecord, SoilNutrientRecord

def test_logging_setup_creates_file():
    """Verify that setup_logging() actually creates the log file on disk."""
    setup_logging()
    config = get_config()
    log_path = Path(config["LOG_PATH"])
    # The file should exist after setup_logging is called
    assert log_path.exists(), f"Log file {log_path} was not created by setup_logging()"

def test_models_import_and_instantiation():
    """Verify that the base data-model classes are defined and usable."""
    # Test RootPhenotypeRecord
    root = RootPhenotypeRecord(species="Arabidopsis thaliana", root_length=12.5)
    assert root.species == "Arabidopsis thaliana"
    assert root.root_length == 12.5

    # Test SoilNutrientRecord
    soil = SoilNutrientRecord(phosphorus=15.0, nitrogen=2.5)
    assert soil.phosphorus == 15.0
    assert soil.nitrogen == 2.5
    assert soil.is_complete_for_analysis() is True

    # Test incomplete record
    incomplete_soil = SoilNutrientRecord(phosphorus=15.0)
    assert incomplete_soil.is_complete_for_analysis() is False

def test_template_exists():
    """Verify that the config template file exists in the project root."""
    template_path = Path("config.yaml.template")
    assert template_path.exists(), "config.yaml.template must exist in the project root"