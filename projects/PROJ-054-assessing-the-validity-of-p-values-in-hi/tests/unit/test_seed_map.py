import json
import os
import sys
import tempfile
from pathlib import Path
import csv
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.generate_seed_map import load_master_seed, load_params, build_seed_map, write_seed_map

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_master_seed_creates_default(temp_dir):
    master_seed_path = temp_dir / 'master_seed.txt'
    seed = load_master_seed(master_seed_path)
    assert seed == 42
    assert master_seed_path.exists()
    with open(master_seed_path, 'r') as f:
        assert f.read().strip() == '42'

def test_load_master_seed_reads_existing(temp_dir):
    master_seed_path = temp_dir / 'master_seed.txt'
    master_seed_path.write_text('123')
    seed = load_master_seed(master_seed_path)
    assert seed == 123

def test_load_master_seed_invalid(temp_dir):
    master_seed_path = temp_dir / 'master_seed.txt'
    master_seed_path.write_text('not_a_number')
    with pytest.raises(ValueError):
        load_master_seed(master_seed_path)

def test_load_params_file_not_found(temp_dir):
    params_path = temp_dir / 'params.csv'
    with pytest.raises(FileNotFoundError):
        load_params(params_path)

def test_load_params_valid(temp_dir):
    params_path = temp_dir / 'params.csv'
    with open(params_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['seed', 'n', 'p', 'rho', 'distribution_type'])
        writer.writeheader()
        writer.writerow({'seed': 1, 'n': 100, 'p': 500, 'rho': 0.5, 'distribution_type': 'normal'})
        writer.writerow({'seed': 2, 'n': 100, 'p': 500, 'rho': 0.5, 'distribution_type': 'normal'})
        writer.writerow({'seed': 3, 'n': 200, 'p': 1000, 'rho': 0.0, 'distribution_type': 't'})

    params = load_params(params_path)
    assert len(params) == 3
    assert params[0]['n'] == 100
    assert params[0]['p'] == 500
    assert params[0]['rho'] == 0.5
    assert params[0]['distribution_type'] == 'normal'
    assert params[0]['seed'] == 1
    assert params[2]['distribution_type'] == 't'

def test_build_seed_map_basic(temp_dir):
    master_seed = 42
    params = [
        {'n': 100, 'p': 500, 'rho': 0.5, 'distribution_type': 'normal', 'seed': 1},
        {'n': 100, 'p': 500, 'rho': 0.5, 'distribution_type': 'normal', 'seed': 2},
        {'n': 200, 'p': 1000, 'rho': 0.0, 'distribution_type': 't', 'seed': 3},
    ]

    seed_map = build_seed_map(params, master_seed)

    key1 = "n=100_p=500_rho=0.5_dist=normal"
    key2 = "n=200_p=1000_rho=0.0_dist=t"

    assert key1 in seed_map
    assert key2 in seed_map
    assert seed_map[key1] == [42, 43]
    assert seed_map[key2] == [44]

def test_build_seed_map_sequential_assignment(temp_dir):
    master_seed = 10
    params = [
        {'n': 10, 'p': 10, 'rho': 0.0, 'distribution_type': 'normal', 'seed': 1},
        {'n': 10, 'p': 10, 'rho': 0.0, 'distribution_type': 'normal', 'seed': 2},
        {'n': 10, 'p': 10, 'rho': 0.0, 'distribution_type': 'normal', 'seed': 3},
    ]

    seed_map = build_seed_map(params, master_seed)
    key = "n=10_p=10_rho=0.0_dist=normal"
    assert seed_map[key] == [10, 11, 12]

def test_write_seed_map(temp_dir):
    seed_map = {
        "key1": [1, 2, 3],
        "key2": [4, 5]
    }
    output_path = temp_dir / 'seed_map.json'
    write_seed_map(seed_map, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded_map = json.load(f)
    assert loaded_map == seed_map