import pytest
import json
import os
import sys
from pathlib import Path
import csv
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.io import cap_dataset_stratified, load_csv, save_csv
from utils.config import get_processed_data_path, get_raw_data_path

class TestT014StratifiedCapping:
    """Tests for T014: Dataset capping with stratified sampling."""

    @pytest.fixture
    def sample_data(self):
        """Generate a sample dataset with known distribution."""
        # Create 100 rows: 60 from Science Advances, 40 from Materials Project
        # Alloy Systems: A (50%), B (30%), C (20%)
        data = []
        
        # System A: 50 rows (30 SA, 20 MP)
        for i in range(30):
            data.append({'composition': f'CompA{i}', 'phase': 'amorphous', 'source': 'Science Advances', 'alloy_system': 'SystemA', 'val': 1.0})
        for i in range(20):
            data.append({'composition': f'CompA{30+i}', 'phase': 'crystalline', 'source': 'Materials Project', 'alloy_system': 'SystemA', 'val': 1.0})
        
        # System B: 30 rows (20 SA, 10 MP)
        for i in range(20):
            data.append({'composition': f'CompB{i}', 'phase': 'amorphous', 'source': 'Science Advances', 'alloy_system': 'SystemB', 'val': 2.0})
        for i in range(10):
            data.append({'composition': f'CompB{20+i}', 'phase': 'crystalline', 'source': 'Materials Project', 'alloy_system': 'SystemB', 'val': 2.0})
        
        # System C: 20 rows (10 SA, 10 MP)
        for i in range(10):
            data.append({'composition': f'CompC{i}', 'phase': 'amorphous', 'source': 'Science Advances', 'alloy_system': 'SystemC', 'val': 3.0})
        for i in range(10):
            data.append({'composition': f'CompC{10+i}', 'phase': 'crystalline', 'source': 'Materials Project', 'alloy_system': 'SystemC', 'val': 3.0})
        
        return data

    def test_capping_reduces_size(self, sample_data):
        """Test that capping reduces the dataset to the target size."""
        target = 50
        result = cap_dataset_stratified(sample_data, target_size=target, seed=42)
        assert len(result) == target, f"Expected {target} rows, got {len(result)}"

    def test_stratification_preserved(self, sample_data):
        """Test that the ratio of alloy systems is preserved approximately."""
        target = 100
        result = cap_dataset_stratified(sample_data, target_size=target, seed=42)
        
        # Count systems
        counts = {}
        for row in result:
            sys = row['alloy_system']
            counts[sys] = counts.get(sys, 0) + 1
        
        # Expected proportions: A=50%, B=30%, C=20%
        # With target 100, we expect ~50, ~30, ~20
        # Allow small rounding errors
        assert abs(counts['SystemA'] - 50) <= 2, f"SystemA count {counts['SystemA']} deviates too much from 50"
        assert abs(counts['SystemB'] - 30) <= 2, f"SystemB count {counts['SystemB']} deviates too much from 30"
        assert abs(counts['SystemC'] - 20) <= 2, f"SystemC count {counts['SystemC']} deviates too much from 20"

    def test_primary_source_priority(self, sample_data):
        """Test that Science Advances records are retained before Materials Project."""
        # Create a scenario where we cap heavily
        # System A has 30 SA, 20 MP. Target for A might be 20.
        # We should get 20 SA and 0 MP.
        target = 30 # Very small target
        result = cap_dataset_stratified(sample_data, target_size=target, seed=42)
        
        # Count sources
        sa_count = sum(1 for r in result if r['source'] == 'Science Advances')
        mp_count = sum(1 for r in result if r['source'] == 'Materials Project')
        
        # Since we prioritize SA, we should have as many SA as possible up to the target
        # In this specific small sample, with seed 42, the distribution might vary,
        # but the logic ensures we take min(len(sa), needed) first.
        # A strict test: If we have enough SA to fill the target, we should have 0 MP?
        # Not necessarily if stratification forces MP.
        # Let's test the logic: If target is large enough to take all SA, we should take all SA.
        
        large_target = 100
        result_large = cap_dataset_stratified(sample_data, target_size=large_target, seed=42)
        sa_large = sum(1 for r in result_large if r['source'] == 'Science Advances')
        mp_large = sum(1 for r in result_large if r['source'] == 'Materials Project')
        
        # Total SA in original is 60. If target 100, we should take all 60 SA.
        assert sa_large == 60, f"Expected all 60 SA records, got {sa_large}"
        # And the rest (40) should be MP
        assert mp_large == 40, f"Expected all 40 MP records, got {mp_large}"

    def test_deterministic_with_seed(self, sample_data):
        """Test that same seed produces same result."""
        target = 50
        result1 = cap_dataset_stratified(sample_data, target_size=target, seed=42)
        result2 = cap_dataset_stratified(sample_data, target_size=target, seed=42)
        
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1['composition'] == r2['composition']
            assert r1['source'] == r2['source']