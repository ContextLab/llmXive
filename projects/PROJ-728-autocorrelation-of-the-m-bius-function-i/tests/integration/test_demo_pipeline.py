import pathlib
import csv
import re

# Import the demo pipeline functions from the code package.
# The code directory is a Python package (contains __init__.py), so we
# import using the package-qualified module names.
from code.generate_mobius import generate_mobius_and_windows
from code.autocorrelation import main as autocorrelation_main

def test_demo_pipeline():
    """
    Integration test that runs the demo pipeline:
    1. Generate the Möbius array and the stratified window starts.
    2. Compute the demo autocorrelation (L=1000, h=1) and write the CSV.
    3. Verify that the CSV exists and contains a numeric entry with at
       least six decimal places.
    """
    # Step 1: generate Möbius data and window start indices.
    generate_mobius_and_windows()

    # Step 2: compute the demo autocorrelation.
    autocorrelation_main()

    # Step 3: check that the result file exists.
    result_path = pathlib.Path("data/results/demo_autocorr.csv")
    assert result_path.is_file(), f"Result file not found: {result_path}"

    # Read the CSV and verify the content.
    with result_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # The CSV should have at least one data row.
    assert rows, "Demo autocorrelation CSV is empty."

    # Extract the autocorrelation value from the first row.
    autocorr_str = rows[0].get("autocorrelation")
    assert autocorr_str is not None, "Missing 'autocorrelation' column."

    # Verify the format: a signed or unsigned decimal number with
    # at least six digits after the decimal point.
    pattern = r"^-?\d+\.\d{6,}$"
    assert re.fullmatch(pattern, autocorr_str), (
        f"Autocorrelation value '{autocorr_str}' does not have at least "
        "six decimal places."
    )