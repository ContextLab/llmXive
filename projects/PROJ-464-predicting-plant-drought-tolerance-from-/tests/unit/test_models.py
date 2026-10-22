import pytest
from pydantic import ValidationError
from code.models import RootImage, RSAMetrics, PhysioTrait

def test_root_image_valid():
    img = RootImage(id="img_001", path="data/raw/nppn_images/img1.png", species="Quercus robur")
    assert img.id == "img_001"
    assert img.path.endswith("img1.png")
    assert img.species == "Quercus robur"

def test_root_image_invalid_empty_fields():
    with pytest.raises(ValidationError):
        RootImage(id="", path="   ", species="")

def test_rsa_metrics_valid():
    metrics = RSAMetrics(
        species_id="Quercus robur",
        depth=120.0,
        branching_density=0.75,
        surface_area=340.2
    )
    assert metrics.species_id == "Quercus robur"
    assert metrics.depth > 0
    assert metrics.branching_density > 0
    assert metrics.surface_area > 0

def test_rsa_metrics_negative_values():
    with pytest.raises(ValidationError):
        RSAMetrics(
            species_id="Quercus robur",
            depth=-10.0,
            branching_density=0.5,
            surface_area=300.0
        )
    with pytest.raises(ValidationError):
        RSAMetrics(
            species_id="Quercus robur",
            depth=10.0,
            branching_density=-0.5,
            surface_area=300.0
        )
    with pytest.raises(ValidationError):
        RSAMetrics(
            species_id="Quercus robur",
            depth=10.0,
            branching_density=0.5,
            surface_area=-300.0
        )

def test_physio_trait_valid():
    trait = PhysioTrait(
        species="Quercus robur",
        conductance=250.0,
        photosynthesis=15.2,
        survival_rate=0.85
    )
    assert trait.species == "Quercus robur"
    assert trait.conductance >= 0
    assert trait.photosynthesis >= 0
    assert 0.0 <= trait.survival_rate <= 1.0

def test_physio_trait_negative_conductance():
    with pytest.raises(ValidationError):
        PhysioTrait(
            species="Quercus robur",
            conductance=-5.0,
            photosynthesis=10.0
        )

def test_physio_trait_survival_rate_out_of_bounds():
    with pytest.raises(ValidationError):
        PhysioTrait(
            species="Quercus robur",
            conductance=200.0,
            photosynthesis=12.0,
            survival_rate=1.5
        )
    with pytest.raises(ValidationError):
        PhysioTrait(
            species="Quercus robur",
            conductance=200.0,
            photosynthesis=12.0,
            survival_rate=-0.2
        )