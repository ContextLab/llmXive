"""
Test that ``code/ingestion/download_data.py`` does not contain any
synthetic‑fallback logic (e.g. generating mock data when the real
download fails). The pipeline must fail loudly if the dataset cannot
be fetched.
"""
import pathlib
import re

def test_no_synthetic_fallback():
    """
    Scan the ingestion script for prohibited keywords that would indicate a
    synthetic fallback or mock data generation.
    """
    # Adjust path to find the script relative to the test file
    script_path = pathlib.Path(__file__).resolve().parents[1] / "ingestion" / "download_data.py"
    
    if not script_path.exists():
        # Fallback for different execution environments
        script_path = pathlib.Path(__file__).resolve().parents[2] / "code" / "ingestion" / "download_data.py"

    content = script_path.read_text(encoding="utf-8").lower()

    # Patterns that would represent a synthetic fallback
    # We allow 'random' if it's part of a library name, but not as a call to generate data
    forbidden_patterns = [
        r"synthetic",
        r"mock",
        r"generate_.*_data",
        r"np\.random\.",
        r"random\.uniform",
        r"random\.randint",
    ]

    matches = [pat for pat in forbidden_patterns if re.search(pat, content)]
    assert not matches, f"Found prohibited fallback patterns in download_data.py: {matches}"