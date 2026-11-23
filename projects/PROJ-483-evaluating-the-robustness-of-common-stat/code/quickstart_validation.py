"""
Quickstart validation helper.
Executes the main pipeline entry point to ensure that the
quickstart steps run without errors.
"""
# Import the main entry point from the project's root `code/main.py`.
# The module name is `main` because the file lives directly under `code/`.
from main import main

if __name__ == "__main__":
    # Run the full pipeline with the default (download) action.
    # This will fetch the datasets, validate them, compute theoretical power,
    # and write the validation & power reports under `results/`.
    main()
