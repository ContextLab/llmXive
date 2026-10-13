import pytest
from code.utils.seeds import get_seed, set_seed

def test_get_seed_consistency():
    task_id = "T015a"
    seed1 = get_seed(task_id)
    seed2 = get_seed(task_id)
    assert seed1 == seed2, "get_seed should return a consistent value for the same task_id"

def test_set_seed_affects_random():
    task_id = "T015a"
    set_seed(task_id)
    import random
    val1 = random.random()
    set_seed(task_id)
    import random as random2
    val2 = random2.random()
    assert val1 == val2, "set_seed should make random deterministic for the same task_id"