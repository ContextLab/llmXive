"""Initialize the test directory tree for PROJ-191 (task T001-C-INIT-TEST).

Creates tests/unit/, tests/contract/, and tests/integration/ under the
project root, plus __init__.py files so pytest can collect them.
"""
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def main() -> None:
    for sub in ("unit", "contract", "integration"):
        d = paths.path("tests", sub)
        d.mkdir(parents=True, exist_ok=True)
        init = d / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
        log.info("Ensured directory: %s", d)
    root_init = paths.path("tests", "__init__.py")
    if not root_init.exists():
        root_init.write_text("", encoding="utf-8")
    log.info("Test directory tree initialized.")


if __name__ == "__main__":
    main()