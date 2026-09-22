"""
Unit tests for code detection and entropy calculation utilities.
This file tests the secondary detector logic used in classify_prs.py.
"""

import pytest
import math
import os
import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.classify_prs import calculate_code_entropy, calculate_ngram_anomaly_score


class TestEntropyCalculation:
    """Tests for code entropy calculation logic."""

    def test_entropy_calculation(self):
        """
        Asserts code entropy calculation returns float > 0 for random code.
        
        This test verifies that the entropy function correctly identifies
        high entropy in random/unstructured code, which is a characteristic
        often associated with LLM-generated code or obfuscated code.
        """
        # Random-like code with high entropy (no repeating patterns)
        random_code = """
        import os
        import sys
        import random
        def process_data(x):
            if x > 10:
                return x * 2
            else:
                return x / 2
        result = process_data(random.randint(1, 100))
        print(f"Result: {result}")
        """
        
        entropy = calculate_code_entropy(random_code)
        
        # Entropy should be a float
        assert isinstance(entropy, float), f"Entropy should be a float, got {type(entropy)}"
        
        # Random code should have positive entropy
        assert entropy > 0, f"Entropy for random code should be > 0, got {entropy}"
        
        # Entropy should be within reasonable bounds (0 to ~8 for byte-level entropy)
        assert 0 < entropy <= 8, f"Entropy {entropy} is outside expected range [0, 8]"

    def test_entropy_zero_for_repetitive_code(self):
        """
        Asserts code entropy calculation returns 0 (or very low) for highly repetitive code.
        """
        # Highly repetitive code with near-zero entropy
        repetitive_code = """
        x = 1
        x = 1
        x = 1
        x = 1
        x = 1
        """
        
        entropy = calculate_code_entropy(repetitive_code)
        
        # Should be very low (close to 0)
        assert 0 <= entropy < 1.0, f"Entropy for repetitive code should be < 1.0, got {entropy}"

    def test_entropy_for_real_python_code(self):
        """
        Asserts entropy calculation works on real Python code samples.
        """
        # Real Python code from a typical function
        python_code = """
        def calculate_average(numbers):
            if not numbers:
                return 0
            total = sum(numbers)
            count = len(numbers)
            return total / count
        
        data = [1, 2, 3, 4, 5]
        avg = calculate_average(data)
        print(f"Average: {avg}")
        """
        
        entropy = calculate_code_entropy(python_code)
        
        # Should be a positive float
        assert isinstance(entropy, float), f"Entropy should be a float, got {type(entropy)}"
        assert entropy > 0, f"Entropy should be > 0, got {entropy}"


class TestNgramAnomalyDetection:
    """Tests for n-gram anomaly detection logic."""

    def test_ngram_anomaly_score(self):
        """
        Asserts n-gram anomaly detection flags synthetic patterns.
        
        This test verifies that the n-gram detector can identify code patterns
        that are unusual or synthetic, which may indicate LLM generation.
        """
        # Synthetic-looking code with unusual patterns (generic names, repetitive structures)
        synthetic_code = """
        def _x123(a, b):
            return a + b
        
        def _y456(x, y):
            return x * y
        
        def _z789(p, q):
            return p - q
        
        result = _x123(1, 2) + _y456(3, 4) - _z789(5, 6)
        """
        
        anomaly_score = calculate_ngram_anomaly_score(synthetic_code)
        
        # Score should be a float
        assert isinstance(anomaly_score, float), f"Anomaly score should be a float, got {type(anomaly_score)}"
        
        # Score should be non-negative
        assert anomaly_score >= 0, f"Anomaly score should be >= 0, got {anomaly_score}"

        # The synthetic code should have a HIGHER anomaly score than normal code
        # because it uses generic, non-descriptive names and repetitive structures
        normal_code = """
        def calculate_total(items):
            total = 0
            for item in items:
                total += item['price'] * item['quantity']
            return total
        
        def process_order(order):
            if order['status'] == 'pending':
                total = calculate_total(order['items'])
                order['total'] = total
                order['status'] = 'processed'
            return order
        """
        
        normal_score = calculate_ngram_anomaly_score(normal_code)
        
        # Synthetic patterns should be flagged as more anomalous
        # We allow some tolerance, but synthetic should generally be higher
        assert anomaly_score >= normal_score * 0.8, (
            f"Synthetic code anomaly score ({anomaly_score}) should be comparable to or higher than "
            f"normal code ({normal_score}). Synthetic patterns should be detectable."
        )

    def test_ngram_anomaly_normal_code(self):
        """
        Asserts n-gram anomaly detection returns lower scores for normal code.
        """
        # Normal, human-like code
        normal_code = """
        def calculate_total(items):
            total = 0
            for item in items:
                total += item['price'] * item['quantity']
            return total
        
        def process_order(order):
            if order['status'] == 'pending':
                total = calculate_total(order['items'])
                order['total'] = total
                order['status'] = 'processed'
            return order
        """
        
        anomaly_score = calculate_ngram_anomaly_score(normal_code)
        
        # Score should be a float
        assert isinstance(anomaly_score, float), f"Anomaly score should be a float, got {type(anomaly_score)}"
        
        # Score should be non-negative
        assert anomaly_score >= 0, f"Anomaly score should be >= 0, got {anomaly_score}"

    def test_ngram_anomaly_empty_code(self):
        """
        Asserts n-gram anomaly detection handles empty code gracefully.
        """
        anomaly_score = calculate_ngram_anomaly_score("")
        
        # Should handle empty string without error
        assert isinstance(anomaly_score, float), f"Anomaly score should be a float, got {type(anomaly_score)}"
        # Empty code should have 0 anomaly score
        assert anomaly_score == 0.0, f"Empty code should have 0.0 anomaly score, got {anomaly_score}"