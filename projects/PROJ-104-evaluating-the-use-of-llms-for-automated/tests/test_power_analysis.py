import pathlib

from llmxive_toolkit import paths

def test_power_report_exists():
    report_path = paths.results("power_report.md")
    assert report_path.is_file(), "Power report markdown file not found."

    text = report_path.read_text(encoding="utf-8")
    # Look for a numeric power estimate line
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    power_line = next((ln for ln in lines if ln.startswith("- estimated_power_n")), None)
    assert power_line is not None, "Power estimate line missing in report."

    # Extract the numeric value
    try:
        _, value = power_line.split(":")
        power_val = float(value.strip())
    except Exception as exc:
        raise AssertionError(f"Could not parse power value: {exc}")

    # Power must be between 0 and 1
    assert 0.0 <= power_val <= 1.0, f"Power out of bounds: {power_val}"

    # Verify exploratory flag matches power
    exploratory_line = next((ln for ln in lines if ln.startswith("- exploratory")), None)
    assert exploratory_line is not None, "Exploratory flag line missing."
    flag_val = exploratory_line.split(":")[1].strip().lower()
    expected = "true" if power_val < 0.8 else "false"
    assert flag_val == expected, f"Exploratory flag mismatch: got {flag_val}, expected {expected}"
