"""Contract test that validates the quickstart.md file format."""
import pathlib
import re

def test_quickstart_file():
    qs_path = pathlib.Path(__file__).parents[2] / "specs" / "001-investigating-the-stability-of-rotating" / "quickstart.md"
    assert qs_path.is_file(), "quickstart.md not found"
    lines = qs_path.read_text(encoding="utf-8").splitlines()
    cmd_lines = [l for l in lines if l.strip().startswith("```") is False and l.strip()]
    # Expect exactly three non‑empty command lines.
    assert len(cmd_lines) == 3, f"Expected 3 commands, found {len(cmd_lines)}"
    for line in cmd_lines:
        assert re.match(r"^bash\\s+.+$", line) or re.match(r"^python\\s+.+$", line), f"Invalid command format: {line}"
