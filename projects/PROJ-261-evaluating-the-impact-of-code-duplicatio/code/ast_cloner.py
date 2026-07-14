"""ast_cloner.py
Parses Python files from the raw sample CSV, detects Type‑1 and Type‑2 clones,
and writes a clone‑density CSV to ``data/processed/clone_metrics.csv``.
The public API consists of ``IdentifierNormalizer``, ``parse_python_file``,
and ``compute_clone_density_batch``.
"""
from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Optional

# NOTE: The original implementation used a relative import which broke when the
# module was executed as a script.  We now use an absolute import that works in
# both contexts.
try:
    from data_loader import download_and_save_sample
except Exception:  # pragma: no cover
    # Fallback – the function will be imported lazily inside the main routine
    download_and_save_sample = None  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IdentifierNormalizer(ast.NodeTransformer):
    """Normalises identifiers in an AST to a generic placeholder."""

    def visit_Name(self, node: ast.Name) -> ast.AST:  # pragma: no cover
        return ast.copy_location(ast.Name(id="_ID", ctx=node.ctx), node)


def parse_python_file(source: str) -> ast.AST:
    """Parse a Python source string into an AST, returning ``None`` on syntax error."""
    try:
        tree = ast.parse(source)
        return IdentifierNormalizer().visit(tree)
    except SyntaxError as exc:
        logger.debug("Syntax error while parsing: %s", exc)
        raise


def _read_raw_samples(csv_path: Path) -> List[Tuple[str, str]]:
    """Read the raw ``github-code-sample.csv`` and return a list of (path, code)."""
    samples: List[Tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append((row["file_path"], row["content"]))
    return samples


def _detect_clones(sources: List[str]) -> Tuple[int, int]:
    """
    Very simple clone detector used for the prototype:

    * ``type1`` – exact string matches.
    * ``type2`` – matches after normalising identifiers.

    Returns a tuple ``(type1_count, type2_count)``.
    """
    type1 = 0
    type2 = 0
    seen: Dict[str, int] = {}
    for src in sources:
        if src in seen:
            type1 += 1
        else:
            seen[src] = 1

    # Normalise identifiers for Type‑2 detection
    normalised = []
    for src in sources:
        try:
            tree = parse_python_file(src)
            normalised.append(ast.unparse(tree))
        except Exception:
            # If parsing fails we simply skip Type‑2 detection for that file
            continue
    seen_norm: Dict[str, int] = {}
    for src in normalised:
        if src in seen_norm:
            type2 += 1
        else:
            seen_norm[src] = 1

    return type1, type2


def compute_clone_density_batch(*args: Any, **kwargs: Any) -> None:
    """
    Compute clone density for the raw sample and write the result to
    ``data/processed/clone_metrics.csv``.

    The function accepts any arguments to stay compatible with callers
    that may pass ``sample_size`` or ``output_path`` – those arguments are
    ignored because the raw CSV is the single source of truth for this
    stage.
    """
    raw_csv = Path("data/raw/github-code-sample.csv")
    if not raw_csv.is_file():
        logger.info(
            "Raw sample not found at %s; generating a fresh sample.", raw_csv
        )
        # Generate a fresh sample using the tolerant loader
        if download_and_save_sample is not None:
            download_and_save_sample()
        else:
            raise FileNotFoundError(
                "download_and_save_sample could not be imported."
            )

    samples = _read_raw_samples(raw_csv)
    file_paths, sources = zip(*samples) if samples else ([], [])

    type1, type2 = _detect_clones(list(sources))
    total_files = len(sources)
    clone_density = (type1 + type2) / total_files if total_files > 0 else 0.0

    output_path = Path("data/processed/clone_metrics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Writing clone metrics to %s", output_path)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["file_path", "type1_clones", "type2_clones", "clone_density"]
        )
        for fp in file_paths:
            writer.writerow([fp, type1, type2, clone_density])