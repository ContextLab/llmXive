import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.data.ingestion import filter_by_class_sample_size

def test_filter_by_class_sample_size():
    """Test T016 logic: remove classes with < 1000 samples."""
    # Create mock data
    data = []
    # Class A: 1200 samples (keep)
    for i in range(1200):
        data.append({"id": i, "reaction_type": "ClassA", "target": 0.5})
    # Class B: 500 samples (remove)
    for i in range(1200, 1200+500):
        data.append({"id": i, "reaction_type": "ClassB", "target": 0.6})
    # Class C: 800 samples (remove)
    for i in range(1700, 1700+800):
        data.append({"id": i, "reaction_type": "ClassC", "target": 0.7})
    
    filtered = filter_by_class_sample_size(data, min_samples=1000)
    
    # Check counts
    class_counts = {}
    for r in filtered:
        cls = r['reaction_type']
        class_counts[cls] = class_counts.get(cls, 0) + 1
    
    assert 'ClassA' in class_counts
    assert class_counts['ClassA'] == 1200
    assert 'ClassB' not in class_counts
    assert 'ClassC' not in class_counts
    assert len(filtered) == 1200

def test_filter_by_class_sample_size_all_removed():
    """Test when all classes are below threshold."""
    data = []
    for i in range(500):
        data.append({"id": i, "reaction_type": "SmallClass", "target": 0.5})
    
    filtered = filter_by_class_sample_size(data, min_samples=1000)
    assert len(filtered) == 0

def test_filter_by_class_sample_size_none_removed():
    """Test when all classes are above threshold."""
    data = []
    for i in range(1500):
        data.append({"id": i, "reaction_type": "BigClass", "target": 0.5})
    
    filtered = filter_by_class_sample_size(data, min_samples=1000)
    assert len(filtered) == 1500
    assert filtered[0]['reaction_type'] == 'BigClass'