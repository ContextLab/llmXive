import importlib
import sys
import pathlib

def test_seed_is_imported_first():
    """
    Ensure that every pipeline script imports `seed` as the first import.
    This test imports the target modules and inspects their source
    to verify that the line ``import seed`` appears before any other
    import statement.
    """
    # List of modules that must import seed first
    modules = [
        "create_dirs",
        "power_analysis",
        "pipeline",
        "ingest",
    ]

    for mod_name in modules:
        # Import the module (relative to the project root)
        full_name = f"code.{mod_name}"
        module = importlib.import_module(full_name)

        # Retrieve the source file
        source_path = pathlib.Path(module.__file__).resolve()
        source = source_path.read_text(encoding="utf-8").splitlines()

        # Find the first non‑empty, non‑comment line
        first_code_line = next(
            (line for line in source if line.strip() and not line.strip().startswith("#")),
            None,
        )
        assert first_code_line is not None, f"{mod_name} appears empty"
        assert first_code_line.strip() == "import seed", f"{mod_name} does not import seed first"