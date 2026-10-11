"""Project scaffold: create all required directories and .gitkeep files.

Run: python code/scaffold.py
Creates code/, data/raw/, data/processed/, models/, metrics/, logs/,
reports/, tests/, contracts/ (and code/utils/, tests/unit, tests/integration)
with .gitkeep placeholders so empty directories are tracked in git.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "models",
    "metrics",
    "logs",
    "reports",
    "tests",
    "tests/unit",
    "tests/integration",
    "contracts",
]


def main() -> None:
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()
            print(f"created {rel}/.gitkeep")
        else:
            print(f"ok      {rel}/.gitkeep")
    print("Scaffold complete.")


if __name__ == "__main__":
    main()
