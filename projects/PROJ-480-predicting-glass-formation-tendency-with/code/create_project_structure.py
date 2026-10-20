"""T001: Create the project directory structure per the implementation plan.

Creates:
    src/data src/models src/reports src/cli src/lib
    tests/contract tests/unit tests/integration
    data/raw data/processed state/ reports/

Each directory is made non-empty with a .gitkeep placeholder file (empty
directories cannot be tracked by git), and a manifest listing every
required directory, its existence status, and its file count is written
to state/directory_manifest.txt as verifiable evidence.
"""

from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "src/data",
    "src/models",
    "src/reports",
    "src/cli",
    "src/lib",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "state",
    "reports",
]


def create_directories(root: Path) -> list:
    """Create all required directories and place .gitkeep in each.

    Args:
        root: The project root directory.

    Returns:
        List of (relative_path, created_now, file_count) tuples.
    """
    manifest = []
    for rel in REQUIRED_DIRS:
        d = root / rel
        created_now = not d.exists()
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not any(d.iterdir()):
            gitkeep.write_text("", encoding="utf-8")
        manifest.append((rel, created_now, len(list(d.iterdir()))))
    return manifest


def write_manifest(root: Path, manifest: list) -> Path:
    """Write the directory manifest to state/directory_manifest.txt."""
    out = root / "state" / "directory_manifest.txt"
    lines = [
        "T001 Project Directory Structure Manifest",
        "=========================================",
        "",
        "Required directory | exists | file_count",
        "-----------------------------------------",
    ]
    for rel, _, count in manifest:
        lines.append(f"{rel} | True | {count}")
    lines += [
        "-----------------------------------------",
        f"Total required directories: {len(manifest)}",
        "All required directories exist: True",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    root = paths.root
    manifest = create_directories(root)
    out = write_manifest(root, manifest)
    print(f"Created/verified {len(manifest)} required directories.")
    print(f"Manifest written to {out}")
    for rel, created_now, count in manifest:
        status = "created" if created_now else "already existed"
        print(f"  {rel}: {status} ({count} entries)")


if __name__ == "__main__":
    main()