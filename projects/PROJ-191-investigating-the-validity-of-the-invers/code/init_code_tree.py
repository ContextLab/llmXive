"""T001-A-INIT-CODE: Create the project code directory tree.

Creates `code/` and its planned subdirectories (data, inference, utils,
robustness, agents) at the repository root, plus the package
`__init__.py` files, so subsequent implementation tasks have a place
to live. Idempotent: safe to re-run.
"""
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

SUBDIRS = [
    "data",
    "inference",
    "utils",
    "robustness",
    "agents",
]

PACKAGES = ["data", "inference", "utils", "robustness", "agents"]


def main() -> None:
    code_root = paths.code()
    for sub in SUBDIRS:
        (code_root / sub).mkdir(parents=True, exist_ok=True)
    for pkg in PACKAGES:
        init_file = code_root / pkg / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                f'"""{pkg} package for the inverse-square-law analysis pipeline."""\n'
            )
    root_init = code_root / "__init__.py"
    if not root_init.exists():
        root_init.write_text(
            '"""Code for investigating the validity of the inverse-square law."""\n'
        )
    log.info("Code directory tree ready at %s", code_root)
    for sub in SUBDIRS:
        log.info("  directory: %s", (code_root / sub))


if __name__ == "__main__":
    main()