"""T001: Create the project structure per the implementation plan.

Creates the full directory tree and package files documented in
specs/001-empirical-analysis-of-twin-prime-gaps-up/plan.md:

    code/            (Python package with __init__.py)
    data/raw/        data/results/        data/figures/
    tests/unit/      tests/integration/   (pytest packages)
    contracts/       paper/

plus a README.md describing the pipeline. The script is idempotent:
re-running it never destroys or overwrites existing data artifacts.
"""
import sys
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root

DIRECTORIES = [
    "code",
    "data/raw",
    "data/results",
    "data/figures",
    "tests/unit",
    "tests/integration",
    "contracts",
    "paper",
]

INIT_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]

GITKEEP_DIRS = ["data/raw", "data/results", "data/figures", "contracts"]

README_LINES = [
    "# Empirical Analysis of Twin Prime Gaps up to 10^9",
    "",
    "This project empirically tests whether the normalized gaps between",
    "consecutive twin-prime pairs, delta_n / log(p_n), follow the exponential",
    "distribution predicted by a Cramer-type random model, and whether",
    "systematic deviations appear near powers of two.",
    "",
    "## Pipeline",
    "",
    "1. **Generate**: `python code/generate_primes.py` produces",
    "   `data/raw/twin_primes.csv` (columns `p`, `p_next`, `delta`,",
    "   `normalized_gap`) using `primesieve`.",
    "2. **Validate**: `python code/validate_schema.py` checks the CSV against",
    "   `contracts/twin_prime_schema.schema.yaml` (blocking gate).",
    "3. **Analyze**: `python code/analyze_gaps.py` runs a Parametric Bootstrap",
    "   Kolmogorov-Smirnov test against Exponential(1) and a QQ-plot;",
    "   `python code/analyze_local.py` runs one-sample t-tests in windows",
    "   [2^k - 10^4, 2^k + 10^4].",
    "4. **Hash**: `python code/hash_artifacts.py` records SHA-256 hashes of all",
    "   artifacts in the project state YAML.",
    "5. **Report**: `python code/verify_citations.py` and `python code/report.py`",
    "   verify citations and compile `paper/analysis_report.md`.",
    "",
    "## Requirements",
    "",
    "Python 3.11+ with `primesieve`, `numpy`, `pandas`, `scipy`, `matplotlib`,",
    "`pyyaml`, and `jsonschema` (see `requirements.txt`). CPU-only execution;",
    "the full pipeline is designed to run in under 45 minutes with peak RAM",
    "below 2 GiB.",
    "",
    "## Tests",
    "",
    "```bash",
    "python -m pytest tests/",
    "```",
    "",
]

GITIGNORE_LINES = [
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "venv/",
    ".pytest_cache/",
    "*.egg-info/",
]


def create_directories() -> None:
    for d in DIRECTORIES:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
        print(f"directory ready: {d}")


def create_init_files() -> None:
    for rel in INIT_FILES:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                '"""Package marker for the twin prime gap analysis project."""\n',
                encoding="utf-8",
            )
            print(f"created: {rel}")
        else:
            print(f"exists:  {rel}")


def create_gitkeeps() -> None:
    for d in GITKEEP_DIRS:
        keeper = ROOT / d / ".gitkeep"
        if not keeper.exists():
            keeper.write_text("", encoding="utf-8")
            print(f"created: {d}/.gitkeep")


def create_readme() -> None:
    readme = ROOT / "README.md"
    if readme.exists():
        print("exists:  README.md (not overwritten)")
        return
    readme.write_text("\n".join(README_LINES), encoding="utf-8")
    print("created: README.md")


def create_gitignore() -> None:
    gi = ROOT / ".gitignore"
    if gi.exists():
        print("exists:  .gitignore (not overwritten)")
        return
    gi.write_text("\n".join(GITIGNORE_LINES) + "\n", encoding="utf-8")
    print("created: .gitignore")


def verify_structure() -> bool:
    missing = [d for d in DIRECTORIES if not (ROOT / d).is_dir()]
    missing += [f for f in INIT_FILES if not (ROOT / f).is_file()]
    if missing:
        print(f"STRUCTURE INCOMPLETE, missing: {missing}", file=sys.stderr)
        return False
    print("Project structure verified: all directories and package files present.")
    return True


def main() -> int:
    print(f"Project root: {ROOT}")
    create_directories()
    create_init_files()
    create_gitkeeps()
    create_readme()
    create_gitignore()
    if not verify_structure():
        return 1
    print("T001 project structure setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())