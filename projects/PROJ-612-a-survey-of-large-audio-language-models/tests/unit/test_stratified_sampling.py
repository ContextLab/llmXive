import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from stratified_sampling import (
    load_captions, 
    load_hallucination_rates, 
    stratified_sample, 
    save_sampling_pool,
    DEFAULT_SAMPLE_SIZE
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_captions(temp_dir):
    data = [
        {"id": 1, "domain": "speech", "text": "hello"},
        {"id": 2, "domain": "music", "text": "la la"}
    ]
    path = temp_dir / "captions.json"
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    result = load_captions(path)
    assert len(result) == 2
    assert result[0]['id'] == 1
    assert result[1]['domain'] == 'music'

def test_load_hallucination_rates(temp_dir):
    csv_content = """domain,rate,ci_lower,ci_upper
    speech,0.1,0.05,0.15
    music,0.2,0.1,0.3
    env,0.15,0.08,0.22"""
    path = temp_dir / "rates.csv"
    path.write_text(csv_content)
    
    result = load_hallucination_rates(path)
    assert 'speech' in result
    assert result['speech'] == 0.1
    assert result['music'] == 0.2
    assert result['env'] == 0.15

def test_stratified_sample_distribution(temp_dir):
    # Create a dataset with known distribution
    # 100 speech, 50 music, 50 env -> Total 200
    # Proportions: 0.5, 0.25, 0.25
    # Sample size 100 -> Expected: 50 speech, 25 music, 25 env
    captions = []
    for i in range(100):
        captions.append({"id": i, "domain": "speech", "text": "s"})
    for i in range(100, 150):
        captions.append({"id": i, "domain": "music", "text": "m"})
    for i in range(150, 200):
        captions.append({"id": i, "domain": "env", "text": "e"})
    
    rates = {"speech": 0.1, "music": 0.2, "env": 0.15}
    
    sampled = stratified_sample(captions, rates, total_n=100)
    
    domains = [item['domain'] for item in sampled]
    counts = {
        'speech': domains.count('speech'),
        'music': domains.count('music'),
        'env': domains.count('env')
    }
    
    assert len(sampled) == 100
    # Allow small variance due to rounding logic in implementation
    assert 45 <= counts['speech'] <= 55
    assert 20 <= counts['music'] <= 30
    assert 20 <= counts['env'] <= 30

def test_stratified_sample_small_dataset(temp_dir):
    # Test with fewer items than requested sample size
    captions = [
        {"id": 1, "domain": "speech", "text": "s"},
        {"id": 2, "domain": "music", "text": "m"}
    ]
    rates = {"speech": 0.1, "music": 0.2}
    
    # Request 100, but only 2 exist
    sampled = stratified_sample(captions, rates, total_n=100)
    
    assert len(sampled) == 2
    assert all(item in captions for item in sampled)

def test_save_sampling_pool(temp_dir):
    samples = [{"id": 1, "domain": "speech"}, {"id": 2, "domain": "music"}]
    path = temp_dir / "pool.json"
    
    save_sampling_pool(samples, path)
    
    assert path.exists()
    with open(path, 'r') as f:
        loaded = json.load(f)
    assert len(loaded) == 2
    assert loaded[0]['id'] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])