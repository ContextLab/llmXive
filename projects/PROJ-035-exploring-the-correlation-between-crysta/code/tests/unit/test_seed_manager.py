import pytest
import os
import numpy as np
import random
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import init_seed, get_seed, is_seed_initialized, add_seed_argument
import argparse

class TestSeedManager:
    def test_init_seed_sets_environment(self):
        seed = init_seed(42)
        assert seed == 42
        assert os.environ.get("SEED_INITIALIZED") == "true"
        assert os.environ.get("RANDOM_SEED") == "42"

    def test_init_seed_randomizes(self):
        seed = init_seed()
        assert seed is not None
        assert is_seed_initialized()

    def test_seed_reproducibility_numpy(self):
        init_seed(123)
        arr1 = np.random.rand(5)
        
        init_seed(123)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)

    def test_seed_reproducibility_random(self):
        init_seed(456)
        val1 = random.random()
        
        init_seed(456)
        val2 = random.random()
        
        assert val1 == val2

    def test_add_seed_argument(self):
        parser = argparse.ArgumentParser()
        add_seed_argument(parser)
        args = parser.parse_args(['--seed', '999'])
        assert args.seed == 999

    def test_add_seed_argument_default(self):
        parser = argparse.ArgumentParser()
        add_seed_argument(parser)
        args = parser.parse_args([])
        assert args.seed is None