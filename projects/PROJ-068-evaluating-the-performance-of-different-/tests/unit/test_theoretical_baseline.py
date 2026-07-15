import pytest
import math
import os
import sys
import csv
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.benchmarks.theoretical_baseline import (
    calculate_optimal_k,
    calculate_optimal_bits,
    calculate_theoretical_memory_bits,
    calculate_theoretical_latency_bounds,
    generate_theoretical_baselines,
    write_theoretical_baselines_csv,
    write_theoretical_baselines_json,
    FPR_TARGETS,
    DATASET_SIZES,
    IMPLEMENTATIONS
)

class TestOptimalK:
    def test_optimal_k_for_fpr_0_01(self):
        """Test optimal k calculation for FPR = 0.01"""
        k = calculate_optimal_k(0.01)
        # -log2(0.01) = 6.64, rounded to 7
        assert k == 7

    def test_optimal_k_for_fpr_0_05(self):
        """Test optimal k calculation for FPR = 0.05"""
        k = calculate_optimal_k(0.05)
        # -log2(0.05) = 4.32, rounded to 4
        assert k == 4

    def test_optimal_k_for_fpr_0_10(self):
        """Test optimal k calculation for FPR = 0.10"""
        k = calculate_optimal_k(0.10)
        # -log2(0.10) = 3.32, rounded to 3
        assert k == 3

    def test_optimal_k_minimum(self):
        """Test that optimal k is at least 1"""
        k = calculate_optimal_k(0.99)
        assert k >= 1

class TestOptimalBits:
    def test_optimal_bits_formula(self):
        """Test the optimal bits formula: m = -n * ln(p) / (ln(2)^2)"""
        n = 100000
        p = 0.01
        ln_2 = math.log(2)
        expected = -n * math.log(p) / (ln_2 ** 2)
        actual = calculate_optimal_bits(n, p)
        # Allow small rounding difference
        assert abs(actual - expected) < 1

    def test_optimal_bits_scaling(self):
        """Test that optimal bits scales linearly with n"""
        p = 0.01
        m1 = calculate_optimal_bits(10000, p)
        m2 = calculate_optimal_bits(100000, p)
        # m2 should be approximately 10x m1
        assert abs(m2 / m1 - 10) < 0.1

    def test_optimal_bits_invalid_p(self):
        """Test that invalid p values raise ValueError"""
        with pytest.raises(ValueError):
            calculate_optimal_bits(1000, 0)
        with pytest.raises(ValueError):
            calculate_optimal_bits(1000, 1)

class TestTheoreticalMemory:
    def test_memory_bits_calculation(self):
        """Test theoretical memory bits calculation"""
        n = 100000
        p = 0.01
        m = calculate_theoretical_memory_bits(n, p, 'BitsetBloomFilter')
        expected = calculate_optimal_bits(n, p)
        assert m == expected

    def test_memory_consistency_across_implementations(self):
        """Test that theoretical memory is consistent across implementations"""
        n = 100000
        p = 0.01
        
        m_array = calculate_theoretical_memory_bits(n, p, 'ArrayBloomFilter')
        m_vector = calculate_theoretical_memory_bits(n, p, 'VectorBloomFilter')
        m_bitset = calculate_theoretical_memory_bits(n, p, 'BitsetBloomFilter')
        
        # All should return the same theoretical minimum
        assert m_array == m_vector == m_bitset

class TestTheoreticalLatency:
    def test_latency_bounds_structure(self):
        """Test that latency bounds dictionary has correct structure"""
        bounds = calculate_theoretical_latency_bounds(100000, 7, 'BitsetBloomFilter')
        
        assert 'insert_latency_us' in bounds
        assert 'query_latency_us' in bounds
        assert 'operations_count' in bounds
        assert bounds['operations_count'] == 14  # 7 hashes + 7 accesses

    def test_latency_scales_with_k(self):
        """Test that latency scales with number of hash functions"""
        bounds_k7 = calculate_theoretical_latency_bounds(100000, 7, 'BitsetBloomFilter')
        bounds_k3 = calculate_theoretical_latency_bounds(100000, 3, 'BitsetBloomFilter')
        
        # Latency should be proportional to k
        assert bounds_k7['operations_count'] > bounds_k3['operations_count']
        assert bounds_k7['insert_latency_us'] > bounds_k3['insert_latency_us']

class TestGenerateBaselines:
    def test_generate_baselines_count(self):
        """Test that generated baselines have correct count"""
        results = generate_theoretical_baselines()
        
        expected_count = len(DATASET_SIZES) * len(FPR_TARGETS) * len(IMPLEMENTATIONS)
        assert len(results) == expected_count

    def test_generate_baselines_structure(self):
        """Test that each baseline has required fields"""
        results = generate_theoretical_baselines()
        
        required_fields = [
            'dataset_size', 'fpr', 'implementation',
            'optimal_bits', 'bits_per_element', 'optimal_k',
            'theoretical_memory_bytes', 'theoretical_memory_bits',
            'theoretical_latency_bounds', 'timestamp'
        ]
        
        for result in results:
            for field in required_fields:
                assert field in result

    def test_generate_baselines_values(self):
        """Test that baseline values are reasonable"""
        results = generate_theoretical_baselines()
        
        # Find a specific configuration
        for result in results:
            if result['dataset_size'] == 100000 and result['fpr'] == 0.01:
                assert result['optimal_k'] == 7
                assert result['bits_per_element'] > 0
                assert result['theoretical_memory_bits'] > 0
                break

class TestWriteBaselines:
    def test_write_csv(self, tmp_path):
        """Test writing baselines to CSV"""
        results = generate_theoretical_baselines()
        output_path = tmp_path / "theoretical_baselines.csv"
        
        write_theoretical_baselines_csv(results, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(results)

    def test_write_json(self, tmp_path):
        """Test writing baselines to JSON"""
        results = generate_theoretical_baselines()
        output_path = tmp_path / "theoretical_baselines.json"
        
        write_theoretical_baselines_json(results, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) == len(results)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
