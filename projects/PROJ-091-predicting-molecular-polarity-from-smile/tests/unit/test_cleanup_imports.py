import pytest
import tempfile
import os
from pathlib import Path
from code.cleanup_imports import (
    get_all_imports,
    get_used_names,
    find_unused_imports,
    remove_unused_imports,
    clean_file
)
import ast

def test_get_all_imports_simple():
    code = """
    import os
    import sys
    from pathlib import Path
    """
    tree = ast.parse(code)
    imports = get_all_imports(tree)
    assert 'os' in imports
    assert 'sys' in imports
    assert 'pathlib' in imports

def test_get_used_names():
    code = """
    import os
    import sys
    x = os.getcwd()
    print(sys.version)
    """
    tree = ast.parse(code)
    used = get_used_names(tree)
    assert 'os' in used
    assert 'sys' in used
    assert 'getcwd' not in used  # Only top-level names
    assert 'version' not in used

def test_find_unused_imports():
    code = """
    import os
    import sys
    import json
    x = os.getcwd()
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        unused = find_unused_imports(temp_path)
        assert 'sys' in unused
        assert 'json' in unused
        assert 'os' not in unused
    finally:
        os.unlink(temp_path)

def test_remove_unused_imports():
    code = """
    import os
    import sys
    import json
    x = os.getcwd()
    """
    unused = ['sys', 'json']
    cleaned = remove_unused_imports('dummy.py', unused)
    assert 'import os' in cleaned
    assert 'import sys' not in cleaned
    assert 'import json' not in cleaned

def test_clean_file(tmp_path):
    code = """
    import os
    import sys
    import json
    x = os.getcwd()
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text(code)

    result = clean_file(str(test_file))
    assert result is True

    cleaned_content = test_file.read_text()
    assert 'import os' in cleaned_content
    assert 'import sys' not in cleaned_content
    assert 'import json' not in cleaned_content

def test_clean_file_no_changes():
    code = """
    import os
    x = os.getcwd()
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        result = clean_file(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)

def test_syntax_error_handling():
    code = """
    import os
    import sys
    x = os.  # Syntax error
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        unused = find_unused_imports(temp_path)
        assert unused == []  # Should return empty list on syntax error
    finally:
        os.unlink(temp_path)