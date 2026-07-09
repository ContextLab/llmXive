import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from extraction.snippet_extractor import (
    TokenCounter, 
    ComplexityCalculator, 
    extract_functions, 
    extract_snippets_from_file, 
    extract_snippets_from_directory
)
import ast

class TestTokenCounter(unittest.TestCase):
    def test_count_tokens_simple(self):
        counter = TokenCounter()
        code = "x = 1"
        # tokenize generates: NAME, OP, NUMBER, NEWLINE, ENDMARKER
        tokens = counter.count_tokens(code)
        self.assertGreater(tokens, 0)

    def test_count_tokens_empty(self):
        counter = TokenCounter()
        self.assertEqual(counter.count_tokens(""), 0)
        self.assertEqual(counter.count_tokens("   "), 0)

class TestComplexityCalculator(unittest.TestCase):
    def test_complexity_simple_function(self):
        calculator = ComplexityCalculator()
        code = "def foo():\n    return 1"
        self.assertEqual(calculator.calculate_complexity(code), 1)

    def test_complexity_if_statement(self):
        calculator = ComplexityCalculator()
        code = """
        def foo(x):
            if x > 0:
                return 1
            return 0
        """
        # 1 (base) + 1 (if) = 2
        self.assertEqual(calculator.calculate_complexity(code), 2)

    def test_complexity_loop_and_if(self):
        calculator = ComplexityCalculator()
        code = """
        def foo(items):
            for item in items:
                if item > 0:
                    print(item)
        """
        # 1 (base) + 1 (for) + 1 (if) = 3
        self.assertEqual(calculator.calculate_complexity(code), 3)

    def test_complexity_bool_op(self):
        calculator = ComplexityCalculator()
        code = """
        def foo(a, b):
            if a and b:
                return True
        """
        # 1 (base) + 1 (if) + 1 (and) = 3
        self.assertEqual(calculator.calculate_complexity(code), 3)

class TestExtractFunctions(unittest.TestCase):
    def test_extract_functions(self):
        code = """
        def func1(): pass
        def func2(): pass
        class Cls:
            def method1(self): pass
        """
        tree = ast.parse(code)
        funcs = extract_functions(tree)
        # Should find func1, func2, method1
        self.assertEqual(len(funcs), 3)
        names = [f.name for f in funcs]
        self.assertIn("func1", names)
        self.assertIn("func2", names)
        self.assertIn("method1", names)

class TestExtractSnippetsFromFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.py"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_snippets_valid_file(self):
        code = """
        def valid_func():
            x = 1
            y = 2
            z = x + y
            if z > 0:
                return z
            return 0
        
        def short_func():
            return 1
        """
        with open(self.test_file, 'w') as f:
            f.write(code)
        
        snippets = extract_snippets_from_file(self.test_file, min_tokens=10)
        
        # Should find valid_func, but short_func might be filtered if tokens < 10
        # Let's check that we get at least one snippet
        self.assertGreater(len(snippets), 0)
        
        # Check structure
        for s in snippets:
            self.assertIn("snippet_content", s)
            self.assertIn("token_count", s)
            self.assertIn("complexity", s)
            self.assertIn("function_name", s)
            self.assertIn("file_path", s)
            self.assertGreater(s["token_count"], 0)
            self.assertGreaterEqual(s["complexity"], 1)

    def test_extract_snippets_syntax_error(self):
        code = "def broken("
        with open(self.test_file, 'w') as f:
            f.write(code)
        
        snippets = extract_snippets_from_file(self.test_file, min_tokens=1)
        self.assertEqual(len(snippets), 0)

    def test_extract_snippets_filter(self):
        # Create a function with very few tokens
        code = "def a(): pass"
        with open(self.test_file, 'w') as f:
            f.write(code)
        
        # High min_tokens should filter it out
        snippets = extract_snippets_from_file(self.test_file, min_tokens=100)
        self.assertEqual(len(snippets), 0)
        
        # Low min_tokens should keep it
        snippets = extract_snippets_from_file(self.test_file, min_tokens=1)
        self.assertGreater(len(snippets), 0)

class TestExtractSnippetsFromDirectory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_snippets_directory(self):
        file1 = self.dir_path / "file1.py"
        file2 = self.dir_path / "file2.py"
        
        code1 = "def f1(): return 1"
        code2 = "def f2(): return 2"
        
        with open(file1, 'w') as f:
            f.write(code1)
        with open(file2, 'w') as f:
            f.write(code2)
        
        snippets = extract_snippets_from_directory(self.dir_path, min_tokens=1)
        
        self.assertEqual(len(snippets), 2)
        names = [s["function_name"] for s in snippets]
        self.assertIn("f1", names)
        self.assertIn("f2", names)

if __name__ == "__main__":
    unittest.main()