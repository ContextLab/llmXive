"""Create the required project directory tree for PROJ-753.

Creates every directory listed in task T001 (with ``.gitkeep``
placeholders so empty directories survive version control) and ensures
the ``code/`` source modules referenced by the task exist on disk.
Existing files are never overwritten.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/results",
    "code",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "docs",
    "reports",
    "figures",
    "scripts",
]

# Source modules the task says code/ must contain. If a module file is
# missing, create it with a module docstring so the tree is complete;
# real implementations arrive in their own tasks and are never clobbered.
CODE_MODULES = {
    "ingest.py": "Ingestion of the Pantheon+ release and residual calculation.",
    "utils.py": "Shared utilities: cosmology helpers and I/O.",
    "spherical_harmonics.py": "HEALPix projection and pseudo-Cl analysis.",
    "simulations.py": "Rotation-based null-distribution simulations.",
    "analysis.py": "Significance assessment and result artifacts.",
    "visualize.py": "Publication-ready figures.",
    "models.py": "Dataclass models for records, pixels and coefficients.",
    "main.py": "End-to-end pipeline entry point.",
}


def main() -> int:
    root: Path = paths.root
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists() and not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.touch()
        print(f"directory ready: {rel}")

    code_dir = root / "code"
    for name, doc in CODE_MODULES.items():
        f = code_dir / name
        if not f.exists():
            f.write_text(f'"""{doc}"""\n', encoding="utf-8")
            print(f"created module stub: code/{name}")
        else:
            print(f"module present: code/{name}")

    print("project tree complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
