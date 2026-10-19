"""
Tests for the Pydantic schemas in ``code/models/schemas.py`` (Task T003).

Verification: sample JSON objects validate against the models without
errors, and invalid objects are rejected.
"""

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from models.schemas import BGCFeature, Metabolite, ModelOutput, Species


SAMPLE_SPECIES = {
    "name": "Arabidopsis thaliana",
    "scientific_name": "Arabidopsis thaliana",
    "clade": "eudicot",
    "genome_path": "data/raw/genomes/athaliana.fna",
    "metabolite_path": "data/raw/metabolites/athaliana.csv",
}

SAMPLE_BGC = {
    "species": "Arabidopsis thaliana",
    "bgc_type": "terpene",
    "presence": True,
    "count": 7,
}

SAMPLE_METABOLITE = {
    "species": "Arabidopsis thaliana",
    "inchikey": "UHQPBOJSSQRHNE-UHFFFAOYSA-N",
    "abundance": 123.4,
    "log_abundance": 4.82,
    "compound_class": "terpenoid",
}

SAMPLE_MODEL_OUTPUT = {
    "algorithm": "RandomForest",
    "hyperparameters": {"n_estimators": 500, "max_depth": 5},
    "r_squared": 0.42,
    "pearson_r": 0.65,
    "p_value": 0.031,
    "cv_method": "LOO",
    "feature_importances": [0.1, 0.4, 0.25, 0.15, 0.1],
}


def test_species_validates_from_json():
    obj = Species.model_validate(json.loads(json.dumps(SAMPLE_SPECIES)))
    assert obj.scientific_name == "Arabidopsis thaliana"
    assert obj.clade == "eudicot"

def test_species_optional_fields_default_to_none():
    obj = Species.model_validate(
        {"name": "Rice", "scientific_name": "Oryza sativa"}
    )
    assert obj.clade is None
    assert obj.genome_path is None
    assert obj.metabolite_path is None

def test_species_rejects_empty_name():
    with pytest.raises(ValidationError):
        Species.model_validate({"name": "  ", "scientific_name": "Oryza sativa"})

def test_bgc_feature_validates_from_json():
    obj = BGCFeature.model_validate(json.loads(json.dumps(SAMPLE_BGC)))
    assert obj.presence is True
    assert obj.count == 7

def test_bgc_feature_rejects_negative_count():
    bad = dict(SAMPLE_BGC)
    bad["count"] = -1
    with pytest.raises(ValidationError):
        BGCFeature.model_validate(bad)

def test_bgc_feature_rejects_empty_type():
    bad = dict(SAMPLE_BGC)
    bad["bgc_type"] = ""
    with pytest.raises(ValidationError):
        BGCFeature.model_validate(bad)

def test_metabolite_validates_from_json():
    obj = Metabolite.model_validate(json.loads(json.dumps(SAMPLE_METABOLITE)))
    assert obj.inchikey == "UHQPBOJSSQRHNE-UHFFFAOYSA-N"
    assert obj.abundance == 123.4

def test_metabolite_rejects_negative_abundance():
    bad = dict(SAMPLE_METABOLITE)
    bad["abundance"] = -0.5
    with pytest.raises(ValidationError):
        Metabolite.model_validate(bad)

def test_metabolite_log_abundance_optional():
    obj = Metabolite.model_validate(
        {
            "species": "Oryza sativa",
            "inchikey": "UHQPBOJSSQRHNE-UHFFFAOYSA-N",
            "abundance": 0.0,
        }
    )
    assert obj.log_abundance is None
    assert obj.compound_class is None

def test_model_output_validates_from_json():
    obj = ModelOutput.model_validate(json.loads(json.dumps(SAMPLE_MODEL_OUTPUT)))
    assert obj.algorithm == "RandomForest"
    assert obj.cv_method == "LOO"
    assert len(obj.feature_importances) == 5

def test_model_output_hyperparameters_default_empty():
    obj = ModelOutput.model_validate(
        {
            "algorithm": "PGLS",
            "r_squared": 0.1,
            "pearson_r": 0.3,
            "p_value": 0.2,
            "cv_method": "5Fold",
        }
    )
    assert obj.hyperparameters == {}
    assert obj.feature_importances is None

def test_model_output_rejects_out_of_range_r_squared():
    bad = dict(SAMPLE_MODEL_OUTPUT)
    bad["r_squared"] = 1.5
    with pytest.raises(ValidationError):
        ModelOutput.model_validate(bad)

def test_model_output_rejects_out_of_range_p_value():
    bad = dict(SAMPLE_MODEL_OUTPUT)
    bad["p_value"] = 1.2
    with pytest.raises(ValidationError):
        ModelOutput.model_validate(bad)

def test_model_output_rejects_empty_algorithm():
    bad = dict(SAMPLE_MODEL_OUTPUT)
    bad["algorithm"] = "   "
    with pytest.raises(ValidationError):
        ModelOutput.model_validate(bad)

def test_all_models_exported():
    import models.schemas as schemas

    assert set(schemas.__all__) == {
        "Species",
        "BGCFeature",
        "Metabolite",
        "ModelOutput",
    }