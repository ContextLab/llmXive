"""Generate a Markdown file summarising all reproducibility log entries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from reproducibility.logs import LogEntry, get_logger


def _format_parameters(params: dict) -> str:
    """Return a compact JSON representation suitable for a Markdown table cell."""
    # Use separators to minimise whitespace; ensure ascii=False to preserve any unicode.
    return json.dumps(params, ensure_ascii=False, separators=(",", ":"))


def generate_operation_logs_md(
    output_path: Path | str = Path("docs/reproducibility/operation_logs.md")
) -> None:
    """
    Write a Markdown report of all logged operations.

    The report contains a table with columns:
      - Timestamp (ISO‑8601 UTC)
      - Operation name
      - Parameters (JSON string)

    Parameters
    ----------
    output_path :
        Destination path for the generated Markdown file. Parent directories are
        created automatically if they do not exist.
    """
    logger = get_logger()
    # Guard against a logger that somehow lacks an ``entries`` attribute.
    entries: Iterable[LogEntry] = getattr(logger, "entries", [])

    # Sort entries chronologically for readability.
    sorted_entries = sorted(entries, key=lambda e: e.timestamp)

    lines = [
        "# Operation Logs",
        "",
        "| Timestamp | Operation | Parameters |",
        "|---|---|---|",
    ]

    for entry in sorted_entries:
        params_str = _format_parameters(entry.parameters)
        # Render parameters inside backticks to preserve formatting.
        lines.append(f"| {entry.timestamp} | {entry.operation} | `{params_str}` |")

    # Ensure the output directory exists.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the Markdown file.
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Entry‑point for ``python -m reproducibility.operation_logs_generator``."""
    generate_operation_logs_md()


if __name__ == "__main__":
    main()