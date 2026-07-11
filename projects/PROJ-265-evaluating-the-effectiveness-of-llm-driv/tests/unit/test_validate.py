import ast
import pytest
import sys
import os
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.validate import (
    check_syntax,
    mock_stdlib_imports,
    count_external_imports,
    validate_function,
)


class TestCheckSyntax:
    """Tests for the check_syntax function."""

    def test_valid_python_code(self):
        """Valid Python code should return True."""
        code = """
        def add(a, b):
            return a + b
        """
        assert check_syntax(code) is True

    def test_invalid_python_syntax(self):
        """Code with SyntaxError should return False."""
        # Missing colon after function definition
        code = """
        def add(a, b)
            return a + b
        """
        assert check_syntax(code) is False

    def test_invalid_python_syntax_mismatched_brackets(self):
        """Code with mismatched brackets should return False."""
        code = """
        def process_list(items):
            result = []
            for item in items:
                if item > 0:
                    result.append(item
            return result
        """
        assert check_syntax(code) is False

    def test_empty_code(self):
        """Empty code string should return True (valid syntax, no content)."""
        assert check_syntax("") is True

    def test_comment_only_code(self):
        """Comment-only code should return True."""
        code = "# This is a comment"
        assert check_syntax(code) is True

    def test_syntax_error_with_indentation(self):
        """Incorrect indentation should return False."""
        code = """
        def test():
            print("hello")
          print("world")
        """
        assert check_syntax(code) is False


class TestMockStdlibImports:
    """Tests for the mock_stdlib_imports function."""

    def test_no_imports(self):
        """Code with no imports should return True."""
        code = """
        def add(a, b):
            return a + b
        """
        assert mock_stdlib_imports(code) is True

    def test_valid_stdlib_import(self):
        """Valid stdlib import should return True."""
        code = """
        import os
        import sys
        from pathlib import Path

        def get_path():
            return Path.home()
        """
        assert mock_stdlib_imports(code) is True

    def test_builtin_function(self):
        """Code using builtins should return True."""
        code = """
        def process(items):
            return list(map(str, items))
        """
        assert mock_stdlib_imports(code) is True

    def test_missing_module_import(self):
        """Import of non-existent module should return False."""
        code = """
        import non_existent_module_xyz

        def test():
            return non_existent_module_xyz.value
        """
        assert mock_stdlib_imports(code) is False

    def test_invalid_module_path(self):
        """Invalid module path should return False."""
        code = """
        from os.path import non_existent_function_xyz

        def test():
            return non_existent_function_xyz()
        """
        assert mock_stdlib_imports(code) is False


class TestCountExternalImports:
    """Tests for the count_external_imports function."""

    def test_no_imports(self):
        """Code with no imports should return 0."""
        code = """
        def add(a, b):
            return a + b
        """
        assert count_external_imports(code) == 0

    def test_stdlib_only(self):
        """Code with only stdlib imports should return 0."""
        code = """
        import os
        import sys
        from pathlib import Path
        from collections import defaultdict
        """
        assert count_external_imports(code) == 0

    def test_single_external_import(self):
        """Code with one external import should return 1."""
        code = """
        import pandas as pd
        """
        assert count_external_imports(code) == 1

    def test_multiple_external_imports(self):
        """Code with multiple external imports should return count."""
        code = """
        import numpy as np
        import pandas as pd
        from sklearn.model import Model
        """
        assert count_external_imports(code) == 3

    def test_mixed_imports(self):
        """Code with mixed stdlib and external imports should count only external."""
        code = """
        import os
        import sys
        import numpy as np
        from pathlib import Path
        import requests
        """
        assert count_external_imports(code) == 2

    def test_external_import_from_statement(self):
        """External imports in 'from' statements should be counted."""
        code = """
        from transformers import pipeline
        from sklearn.utils import check_array
        """
        assert count_external_imports(code) == 2


class TestValidateFunction:
    """Tests for the validate_function function."""

    def test_valid_function(self):
        """A valid function should pass all checks."""
        code = """
        def add(a, b):
            return a + b
        """
        result = validate_function(code)
        assert result["is_valid"] is True
        assert result["reason"] == "valid"

    def test_syntax_error_excluded(self):
        """Functions with syntax errors should be excluded."""
        code = """
        def add(a, b)
            return a + b
        """
        result = validate_function(code)
        assert result["is_valid"] is False
        assert result["reason"] == "syntax_error"

    def test_import_error_excluded(self):
        """Functions with import errors should be excluded."""
        code = """
        import non_existent_module_xyz

        def test():
            return non_existent_module_xyz.value
        """
        result = validate_function(code)
        assert result["is_valid"] is False
        assert result["reason"] == "import_error"

    def test_external_import_limit(self):
        """Functions with too many external imports should be excluded."""
        # More than 3 external imports
        code = """
        import numpy as np
        import pandas as pd
        import sklearn
        import requests
        import torch
        """
        result = validate_function(code)
        assert result["is_valid"] is False
        assert result["reason"] == "too_many_external_imports"

    def test_empty_function_body(self):
        """Function with pass should be valid."""
        code = """
        def empty_function():
            pass
        """
        result = validate_function(code)
        assert result["is_valid"] is True
        assert result["reason"] == "valid"

    def test_complex_valid_function(self):
        """A complex but valid function should pass."""
        code = """
        import os
        import sys
        from pathlib import Path
        from collections import defaultdict

        def process_data(items):
            result = defaultdict(list)
            for item in items:
                if isinstance(item, dict):
                    for k, v in item.items():
                        result[k].append(v)
            return dict(result)
        """
        result = validate_function(code)
        assert result["is_valid"] is True
        assert result["reason"] == "valid"