"""
Verification script for schema validations (T098‑T101).

This script invokes the existing ``check_schema_validations`` function from
``validation.final_validator`` which runs the individual JSON/YAML schema
checks for the raw dataset, elemental properties table, descriptor table, and
processed data artifact.  It raises an exception if any validation fails,
otherwise it writes a simple JSON report indicating success.

The script is intended to be executed as::

    python code/validation/verify_schema_validations.py

and will produce ``output/schema_validation_report.json``.
"""
import os
import json
from validation.final_validator import check_schema_validations

def main() -> None:
    """
    Run schema validation checks and write a pass/fail report.

    Raises
    ------
    RuntimeError
        If any of the schema validations report missing‑field errors or other
        validation failures.
    """
    # ``check_schema_validations`` is expected to raise on failure or return
    # a falsy value.  We defensively handle both behaviours.
    try:
        result = check_schema_validations()
    except Exception as exc:
        raise RuntimeError(f"Schema validation raised an exception: {exc}") from exc

    # If the function returns a value, interpret falsy as failure.
    if result is not None and not result:
        raise RuntimeError("Schema validation reported failures.")

    # Write a minimal success report.
    report_path = os.path.join("output", "schema_validation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"status": "PASS"}, f, indent=2)

    print(f"Schema validation succeeded. Report written to {report_path}")

if __name__ == "__main__":
    main()