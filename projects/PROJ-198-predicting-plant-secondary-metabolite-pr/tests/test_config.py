"""
Unit tests for the configuration loader (T005).
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Ensure we can import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import load_config, get_config, reset_config, get_data_path
from models.species import Species


def create_temp_config(tmp_path: Path) -> Path:
    """Helper to create a valid temporary config file."""
    config_data = {
        "settings": {
            "data_root": str(tmp_path / "data"),
            "phylogeny_path": "raw/phylogeny/tree.newick",
            "mibig_ontology_path": "raw/mibig/ontology.json",
            "max_genome_size_mb": 500.0,
            "antismash_confidence": 0.3,
            "min_species_count": 5,
            "download_timeout": 300
        },
        "species_list": [
            {
                "name": "Test Species",
                "scientific_name": "Testus speciesus",
                "genome_assembly": "v1",
                "source": "TestDB",
                "accession": "TEST001"
            }
        ]
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    return config_file


def test_load_config_success(tmp_path):
    """Test successful loading of a valid config file."""
    config_file = create_temp_config(tmp_path)
    reset_config()
    
    config = load_config(str(config_file))
    
    assert config is not None
    assert config.settings.data_root == config_file.parent / "data"
    assert len(config.species_list) == 1
    assert config.species_objects[0].scientific_name == "Testus speciesus"


def test_get_config_raises_if_not_loaded():
    """Test that get_config raises RuntimeError if config not loaded."""
    reset_config()
    with pytest.raises(RuntimeError, match="Configuration not loaded"):
        get_config()


def test_get_data_path(tmp_path):
    """Test constructing data paths relative to root."""
    config_file = create_temp_config(tmp_path)
    reset_config()
    
    load_config(str(config_file))
    
    data_path = get_data_path("raw/test.txt")
    assert data_path.parts[-3:] == ('data', 'raw', 'test.txt')


def test_invalid_species_skipped():
    """Test that invalid species entries are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_data = {
            "settings": {
                "data_root": str(tmp_path / "data"),
                "phylogeny_path": "raw/tree.newick",
                "mibig_ontology_path": "raw/ontology.json",
                "max_genome_size_mb": 500.0,
                "antismash_confidence": 0.3,
                "min_species_count": 5,
                "download_timeout": 300
            },
            "species_list": [
                {
                    "name": "Valid Species",
                    "scientific_name": "Validus species",
                    "genome_assembly": "v1",
                    "source": "DB",
                    "accession": "ACC1"
                },
                {
                    "name": "Invalid Species",
                    # Missing required fields
                    "genome_assembly": "v1"
                }
            ]
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        reset_config()
        config = load_config(str(config_file))
        
        # Should have 1 valid species, the invalid one should be skipped or logged
        # The current implementation logs a warning and skips
        assert len(config.species_objects) == 1
        assert config.species_objects[0].scientific_name == "Validus species"


def test_config_caching():
    """Test that load_config returns the same instance if called again."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_file = create_temp_config(tmp_path)
        reset_config()
        
        c1 = load_config(str(config_file))
        c2 = load_config(str(config_file))
        
        assert c1 is c2
