import pytest
from pathlib import Path
import tempfile
import os
import sys
from src.metrics import calculate_loc_ast, calculate_loc_batch, main
from src.metrics_pmd import calculate_cc_single_file, calculate_cc_batch
from src.metrics_halstead import tokenize_java, calculate_halstead_volume, calculate_halstead_for_file, calculate_halstead_batch

class TestCyclomaticComplexity:
    """Tests for Cyclomatic Complexity metric (T010a)"""

    def test_cc_returns_int(self):
        """Verify that Cyclomatic Complexity returns an integer value."""
        # Create a simple Java file with known complexity
        java_code = """
        public class SimpleClass {
            public int add(int a, int b) {
                if (a > 0) {
                    return a + b;
                } else {
                    return b;
                }
            }
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_path = f.name
        
        try:
            # Calculate CC for the single file
            result = calculate_cc_single_file(temp_path)
            
            # Verify the result is an integer
            assert isinstance(result, int), f"Expected int, got {type(result)}"
            assert result >= 0, f"CC should be non-negative, got {result}"
            # The simple if-else structure should have CC >= 2
            assert result >= 2, f"Expected CC >= 2 for if-else, got {result}"
        finally:
            os.unlink(temp_path)

class TestHalsteadVolume:
    """Tests for Halstead Volume metric (T010b)"""

    def test_halstead_returns_float(self):
        """Verify that Halstead Volume returns a float value."""
        # Create a simple Java file with known structure
        java_code = """
        public class SimpleClass {
            public int add(int a, int b) {
                int result = a + b;
                return result;
            }
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_path = f.name
        
        try:
            # Calculate Halstead volume for the single file
            result = calculate_halstead_for_file(temp_path)
            
            # Verify the result is a float
            assert isinstance(result, float), f"Expected float, got {type(result)}"
            assert result >= 0.0, f"Volume should be non-negative, got {result}"
            # The simple class should have a positive volume
            assert result > 0.0, f"Expected positive volume, got {result}"
        finally:
            os.unlink(temp_path)

    def test_halstead_complexity_calculation(self):
        """Verify Halstead metrics are calculated correctly for known input."""
        # Simple Java code: int x = 5;
        java_code = """
        public class Test {
            public void test() {
                int x = 5;
            }
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_path = f.name
        
        try:
            # Tokenize and calculate
            tokens = tokenize_java(java_code)
            volume = calculate_halstead_volume(tokens)
            
            # Volume should be a positive float
            assert isinstance(volume, float)
            assert volume > 0.0
        finally:
            os.unlink(temp_path)

    def test_halstead_batch_returns_list_of_floats(self):
        """Verify batch calculation returns list of floats."""
        java_code1 = """
        public class Test1 {
            public void test() { int x = 1; }
        }
        """
        java_code2 = """
        public class Test2 {
            public void test() { int y = 2; }
        }
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "Test1.java")
            file2 = os.path.join(tmpdir, "Test2.java")
            
            with open(file1, 'w') as f:
                f.write(java_code1)
            with open(file2, 'w') as f:
                f.write(java_code2)
            
            results = calculate_halstead_batch([file1, file2])
            
            assert isinstance(results, list)
            assert len(results) == 2
            for vol in results:
                assert isinstance(vol, float)
                assert vol >= 0.0

def test_loc_returns_int():
    """Verify LOC returns integer (complementary to CC test)."""
    java_code = """
    public class Test {
        public void method1() { }
        public void method2() { }
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(java_code)
        temp_path = f.name
    
    try:
        result = calculate_loc_ast(temp_path)
        assert isinstance(result, int)
        assert result >= 0
    finally:
        os.unlink(temp_path)