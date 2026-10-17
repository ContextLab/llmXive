"""Create the project directory skeleton and write directory_structure.txt (T001)."""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DIRECTORIES = [
    "code/",
    "tests/",
    "data/raw/",
    "data/processed/",
    "artifacts/",
    "artifacts/logs/",
]


def main() -> int:
    root = paths.root
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        # Ensure the directory is tracked even in empty form
        keep = d / ".gitkeep"
        if not any(d.iterdir()):
            keep.write_text("")
        log.info("Ensured directory: %s", d)

    listing = root / "directory_structure.txt"
    listing.write_text("\n".join(DIRECTORIES) + "\n")
    log.info("Wrote %s", listing)

    # Verify
    for rel in DIRECTORIES:
        assert (root / rel).is_dir(), f"missing {rel}"
    assert listing.is_file()
    print("\n".join(DIRECTORIES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())