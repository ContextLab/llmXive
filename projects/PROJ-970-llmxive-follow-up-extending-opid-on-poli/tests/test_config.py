import pytest
from config import set_seed, get_seed, get_tier_config

def test_seed_set_and_get():
    set_seed(123)
    assert get_seed() == 123

def test_tier_config_exists():
    config = get_tier_config(1)
    assert "name" in config
    assert config["name"] == "deterministic"
