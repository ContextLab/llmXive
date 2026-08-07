"""
Test for Task T034: Reconcile run-book vs implementation.

Verifies that:
1. docs/quickstart.md references the correct script names.
2. The reconciled scripts (extract_features.py, train_models.py, analyze_results.py) exist.
3. The scripts can be imported and have a main function.
"""

import os
import sys
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DOCS_DIR = PROJECT_ROOT / "docs"

def test_quickstart_references_03_feature_extraction():
    """Verify quickstart.md references code/03_feature_extraction.py"""
    quickstart_path = DOCS_DIR / "quickstart.md"
    assert quickstart_path.exists(), "docs/quickstart.md does not exist"
    
    content = quickstart_path.read_text()
    assert "code/03_feature_extraction.py" in content, \
        "quickstart.md does not reference code/03_feature_extraction.py"

def test_quickstart_references_04_train_orchestrator():
    """Verify quickstart.md references code/04_train_orchestrator.py"""
    quickstart_path = DOCS_DIR / "quickstart.md"
    content = quickstart_path.read_text()
    assert "code/04_train_orchestrator.py" in content, \
        "quickstart.md does not reference code/04_train_orchestrator.py"

def test_extract_features_script_exists():
    """Verify code/extract_features.py exists"""
    script_path = CODE_DIR / "extract_features.py"
    assert script_path.exists(), f"Script {script_path} does not exist"

def test_train_models_script_exists():
    """Verify code/train_models.py exists"""
    script_path = CODE_DIR / "train_models.py"
    assert script_path.exists(), f"Script {script_path} does not exist"

def test_analyze_results_script_exists():
    """Verify code/analyze_results.py exists"""
    script_path = CODE_DIR / "analyze_results.py"
    assert script_path.exists(), f"Script {script_path} does not exist"

def test_extract_features_has_main():
    """Verify code/extract_features.py has a main function"""
    script_path = CODE_DIR / "extract_features.py"
    # Add code dir to path for import
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("extract_features", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main'), "extract_features.py does not have a 'main' function"
    finally:
        sys.path.remove(str(PROJECT_ROOT))

def test_train_models_has_main():
    """Verify code/train_models.py has a main function"""
    script_path = CODE_DIR / "train_models.py"
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("train_models", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main'), "train_models.py does not have a 'main' function"
    finally:
        sys.path.remove(str(PROJECT_ROOT))

def test_analyze_results_has_main():
    """Verify code/analyze_results.py has a main function"""
    script_path = CODE_DIR / "analyze_results.py"
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("analyze_results", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main'), "analyze_results.py does not have a 'main' function"
    finally:
        sys.path.remove(str(PROJECT_ROOT))

def test_scripts_are_syntax_valid():
    """Verify all reconciled scripts are syntactically valid Python"""
    scripts = [
        CODE_DIR / "extract_features.py",
        CODE_DIR / "train_models.py",
        CODE_DIR / "analyze_results.py"
    ]
    for script in scripts:
        with open(script, 'r') as f:
            source = f.read()
        try:
            compile(source, str(script), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {script}: {e}")