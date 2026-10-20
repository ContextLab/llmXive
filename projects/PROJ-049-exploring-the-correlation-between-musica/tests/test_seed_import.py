import pathlib
import pytest

def test_seed_import_first_line():
    """
    Verify that all Python scripts in the code directory import the seed module 
    as their first functional line to ensure deterministic execution.
    """
    code_dir = pathlib.Path("code")
    # Get all .py files in the code directory
    py_files = list(code_dir.glob("*.py"))
    
    # We exclude seed.py itself from the check
    py_files = [f for f in py_files if f.name != "seed.py"]
    
    if not py_files:
        pytest.fail("No pipeline scripts found in code/ to verify.")

    for py_file in py_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Find the first non-empty, non-comment, non-shebang line
            first_functional_line = None
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#!"): # Skip shebang
                    continue
                if stripped.startswith("#"):   # Skip comments
                    continue
                first_functional_line = stripped
                break
            
            assert first_functional_line == "import seed", \
                f"File {py_file} does not start with 'import seed' as its first functional line. Found: {first_functional_line}"

if __name__ == "__main__":
    # Allow running directly via python tests/test_seed_import.py
    try:
        test_seed_import_first_line()
        print("Verification successful: All scripts import seed as the first line.")
    except AssertionError as e:
        print(f"Verification failed: {e}")
        exit(1)