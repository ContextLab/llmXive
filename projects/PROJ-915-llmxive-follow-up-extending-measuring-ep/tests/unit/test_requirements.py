import re
from pathlib import Path

def test_requirements_contains_required_packages():
    """
    Verify that requirements.txt exists and lists at least the required packages.
    """
    req_path = Path("requirements.txt")
    assert req_path.is_file(), "requirements.txt not found"

    content = req_path.read_text()

    required_packages = [
        "datasets",
        "scikit-learn",
        "statsmodels",
        "sentence-transformers",
        "llama-cpp-python",
        "pandas",
        "numpy",
        "tqdm",
        "biopython",
        "firth-logistic",
        "requests",
        "ruff",
        "black",
    ]

    for pkg in required_packages:
        # The line may include version specifiers; we just need the package name at start of line
        pattern = rf"^{re.escape(pkg)}([<>=!].*)?$"
        assert re.search(pattern, content, re.MULTILINE), f"{pkg} not listed in requirements.txt"