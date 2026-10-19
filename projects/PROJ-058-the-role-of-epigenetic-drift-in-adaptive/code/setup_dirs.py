"""Create the project directory skeleton required by task T001c.

Creates (idempotently):
  output/, output/figures/, tests/, tests/unit/, tests/contract/,
  logs/, data/processed/

Run: python code/setup_dirs.py
"""
from llmxive_toolkit import paths

DIRECTORIES = [
    ("output",),
    ("output", "figures"),
    ("tests",),
    ("tests", "unit"),
    ("tests", "contract"),
    ("logs",),
    ("data", "processed"),
]

def main() -> None:
    created = []
    for parts in DIRECTORIES:
        d = paths.path(*parts)
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    if created:
        print("Created directories:")
        for c in created:
            print(f"  {c}")
    else:
        print("All required directories already exist.")
    # Verify all required directories exist; fail loudly otherwise.
    missing = [p for p in (paths.path(*parts) for parts in DIRECTORIES) if not p.is_dir()]
    if missing:
        raise RuntimeError(f"Missing directories after setup: {missing}")
    print("Directory skeleton verified OK.")

if __name__ == "__main__":
    main()