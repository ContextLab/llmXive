"""Create the project directory skeleton for T001.

Creates (idempotently):
  src/{models,services,cli,utils}
  tests/{contract,integration,unit}
  data/{raw,processed}
  artifacts/{results,plots}

Exits non-zero if any required directory is missing after creation.
"""
import sys
from llmxive_toolkit import paths

REQUIRED_DIRS = [
    ("src", "models"),
    ("src", "services"),
    ("src", "cli"),
    ("src", "utils"),
    ("tests", "contract"),
    ("tests", "integration"),
    ("tests", "unit"),
    ("data", "raw"),
    ("data", "processed"),
    ("artifacts", "results"),
    ("artifacts", "plots"),
]

def main() -> int:
    for parts in REQUIRED_DIRS:
        # paths.code(...) resolves under <project>/code/ and creates the folder
        target = paths.code(*parts)
        target.mkdir(parents=True, exist_ok=True)
        if not target.is_dir():
            print(f"FAILED to create: {target}", file=sys.stderr)
            return 1
        print(f"OK {target}")

    # Verification per tasks.md: src/models, tests/unit, data/processed
    checks = [paths.code("src", "models"), paths.code("tests", "unit"), paths.code("data", "processed")]
    if not all(p.is_dir() for p in checks):
        print("Verification failed: required directories missing", file=sys.stderr)
        return 1
    print("Project skeleton created and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())