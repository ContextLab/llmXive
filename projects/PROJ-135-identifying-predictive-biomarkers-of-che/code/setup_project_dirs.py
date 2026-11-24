"""
T001a: Create the project directory structure.

Creates only PROJECT-OWNED directories (code/, data/, results/, tests/,
specs/). The platform-owned `state/` directory is intentionally NOT
created here; artifact hashes and state are managed by the platform.
"""
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Each tuple is (paths.<folder> callable, subpath parts) for a directory
# to create, followed by the .gitkeep marker written inside it.
DIRECTORIES = [
    (paths.code, ("src",)),
    (paths.code, ("src", "scripts")),
    (paths.data, ("raw",)),
    (paths.data, ("processed",)),
    (paths.results, ()),
    (paths.results, ("meta_analysis",)),
    (paths.results, ("de",)),
    (paths.results, ("models",)),
    (paths.results, ("validation",)),
    (paths.results, ("plots",)),
    (paths.results, ("metrics",)),
    (paths.tests, ()),
    (paths.tests, ("unit",)),
    (paths.tests, ("integration",)),
    (paths.tests, ("contract",)),
    (paths.specs, ("001-chemo-biomarker-discovery", "contracts")),
]

def create_directories() -> list:
    """Create each directory (with a .gitkeep marker) and return the
    list of created marker file paths."""
    created = []
    for folder_fn, parts in DIRECTORIES:
        marker = folder_fn(*parts, ".gitkeep")
        marker.write_text("")
        created.append(str(marker))
        log.info("Ensured directory exists: %s", marker.parent)
    return created

def main() -> None:
    created = create_directories()
    log.info("Project directory structure ready (%d directories).",
             len(created))
    for p in created:
        print(p)

if __name__ == "__main__":
    main()