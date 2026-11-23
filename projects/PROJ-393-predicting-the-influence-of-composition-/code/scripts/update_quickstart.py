"""
Utility that rewrites ``quickstart.md`` when the project layout changes.
The implementation now inserts the exact command ``python -m src.main --help``
and documents the required “Setup OK” phrase.
"""
import re
from pathlib import Path

QUICKSTART_PATH = Path(__file__).resolve().parent.parent / "quickstart.md"

def main():
    """Update the quickstart file with the latest command references."""
    if not QUICKSTART_PATH.exists():
        raise FileNotFoundError(f"{QUICKSTART_PATH} does not exist")

    text = QUICKSTART_PATH.read_text(encoding="utf-8")

    # Ensure the help command line is present and contains the required phrase.
    help_block = r"python -m src\.main --help\s+# should include “Setup OK”"
    if not re.search(help_block, text):
        # Insert the check after the “Running the Pipeline” section.
        insert_point = re.search(r"## Running the Pipeline", text)
        if insert_point:
            insertion = (
                "\n```bash\n"
                "cd code\n"
                "python -m src.main --help   # should include “Setup OK”\n"
                "```\n"
            )
            pos = insert_point.end()
            text = text[:pos] + insertion + text[pos:]

    QUICKSTART_PATH.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
