"""Cross-script DATA-SCHEMA contract analysis for the execution-fix loop.

The sibling :mod:`llmxive.execution.shared_contract` turns un-converging CODE-API
contract bugs (a symbol the project defines, called incompatibly by many scripts)
into fixable ones. This module does the same for the OTHER un-converging class:
DATA-SCHEMA mismatches across scripts that exchange a file.

The canonical case is PROJ-262: a PRODUCER ``code/generate_metrics.py`` writes
``results/metrics.csv`` with columns ``[seed, model_type, MAE, RMSE]``, while two
CONSUMERS (``generate_performance_plots.py``, ``generate_significance.py``) require
``[seed, model, mae, rmse]`` and raise ``ValueError: Metrics CSV missing columns:
{'mae','rmse','model'}``; ``generate_summary.py`` then dies with
``FileNotFoundError: results/significance.csv`` (a cascade — that producer never
ran because it failed first). The implementer can't fix it because the execution
feedback only ever shows the failing CONSUMER's traceback — it NEVER shows that
the producer actually wrote ``MAE/RMSE/model_type``. A human reconciles the two in
30 seconds.

From the run-book failures this module:

* detects DATA-contract errors (missing columns / KeyError / not-in-index, and
  ``FileNotFoundError: <intermediate.csv>``) and the DATA FILE each one is about;
* locates the PRODUCER script(s) that WRITE that path and the CONSUMER script(s)
  that READ it;
* reads the ACTUAL artifact on disk (CSV header / parquet columns / json keys) —
  the producer already ran — so the feedback is grounded in REAL data, never a
  guess (Constitution: Verified Accuracy);
* renders implementer feedback (:func:`render_data_contract_feedback`) stating the
  ACTUAL vs REQUIRED schema, the exact rename diff, the producer + consumer
  scripts, and the instruction to pick ONE canonical schema and make the PRODUCER
  write exactly what the consumers read (editing in place);
* exposes :func:`reopen_targets` — the producer/consumer files whose tasks should
  be re-opened — analogous to ``shared_contract.defining_files``;
* mirrors ``shared_contract``'s cumulative ledger so a contract satisfied one round
  is not silently dropped the next (anti-thrash).
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# --- Detection: which COLUMNS/KEYS a consumer requires that are missing. -------
# Group 1 holds a brace/bracket/quoted list of the missing names; ``_parse_names``
# normalises it. These cover pandas + csv.DictReader + plain-dict access patterns.
_MISSING_COLS_PATTERNS = [
    # "missing columns: {'mae', 'rmse', 'model'}" / "missing required columns: {...}"
    re.compile(r"missing(?:\s+required)?\s+columns?:\s*[\{\[]([^}\]]*)[\}\]]", re.IGNORECASE),
    # pandas: "['mae', 'rmse'] not in index"
    re.compile(r"[\[\{]([^\]\}]*)[\]\}]\s+not in index", re.IGNORECASE),
    # generic: "columns not found: {...}" / "column(s) ... missing: [...]"
    re.compile(r"columns?[^:\n]*(?:not found|missing)[^:\n]*:\s*[\{\[]([^}\]]*)[\}\]]", re.IGNORECASE),
]
# A single missing key: "KeyError: 'mae'".
_KEYERROR_PATTERN = re.compile(r"KeyError:\s*['\"]([\w .-]+)['\"]")

# --- Detection: an intermediate data file another script was supposed to write. -
_DATA_EXTS = "csv|parquet|json|npy|npz|pkl|pickle|feather|tsv"
_MISSING_FILE_PATTERNS = [
    re.compile(rf"FileNotFoundError:[^\n]*?([\w./-]+\.(?:{_DATA_EXTS}))", re.IGNORECASE),
    re.compile(r"No such file or directory:\s*['\"]([^'\"]+)['\"]"),
    re.compile(rf"(?:CSV|file|path)[^\n]*?not found[^\n]*?([\w./-]+\.(?:{_DATA_EXTS}))", re.IGNORECASE),
]

# A data-file path mentioned anywhere in a failure block (used to attribute a
# missing-columns error — whose message names no path — to the file the failing
# CONSUMER actually reads).
_DATA_PATH_TOKEN = re.compile(rf"([\w./-]+\.(?:{_DATA_EXTS}))", re.IGNORECASE)
# The source file of a traceback frame, e.g. ``File ".../code/analysis/foo.py", line 51``.
_TRACEBACK_FILE = re.compile(r'File "([^"]*?/code/[\w./-]+\.py)"')

_LEDGER_FILENAME = "data_contract_ledger.json"


@dataclass
class DataContractIssue:
    data_file: str                              # repo-relative-to-code-parent, e.g. results/metrics.csv
    required: list[str] = field(default_factory=list)   # columns/keys the consumer needs
    actual: list[str] | None = None             # real schema on disk (None = file absent)
    producers: list[str] = field(default_factory=list)  # code/*.py that WRITE the file
    consumers: list[str] = field(default_factory=list)  # code/*.py that READ the file
    missing_file: bool = False                  # the file is simply not produced (cascade root)

    def rename_map(self) -> dict[str, str]:
        """Best-effort actual->required rename suggestions (case/alias matches).

        Pairs an actual column with a required one when they match
        case-insensitively (``MAE``->``mae``) or as a known alias
        (``model_type``->``model``). Only columns the consumer is MISSING are
        proposed, so an already-correct column is never "renamed".
        """
        if not self.actual:
            return {}
        actual_lower = {c.lower(): c for c in self.actual}
        out: dict[str, str] = {}
        for req in self.required:
            if req in self.actual:
                continue  # already present, nothing to rename
            rl = req.lower()
            if rl in actual_lower:                       # case-only difference
                out[actual_lower[rl]] = req
                continue
            for alias in _ALIASES.get(rl, ()):           # known semantic alias
                if alias in actual_lower:
                    out[actual_lower[alias]] = req
                    break
        return out


# Conservative, project-agnostic aliases for the case where a rename is more than
# pure case (a real schema drift, not a typo). Keys/values are lower-case. This is
# only a HINT in the feedback — the implementer still decides — so it is safe.
_ALIASES: dict[str, tuple[str, ...]] = {
    "model": ("model_type", "model_name", "modeltype", "modelname"),
    "mae": ("mean_absolute_error", "mae_value"),
    "rmse": ("root_mean_squared_error", "rmse_value"),
}


# An f-string PLACEHOLDER like ``{missing}`` appears verbatim in a traceback's
# source line (``raise ValueError(f"... missing columns: {missing}")``); it is NOT
# a column name. When a fragment is a single bare identifier (no quotes, no comma)
# it is almost certainly such a placeholder, so reject it.
_PLACEHOLDER_HINTS = frozenset({"missing", "cols", "columns", "keys", "names", "diff", "set"})


def _parse_names(blob: str) -> list[str]:
    """Pull column/key names out of a ``{'a', 'b'}`` / ``['a', 'b']`` / ``a, b``
    fragment, preserving order and dropping dups.

    Quote-aware: if the fragment contains any QUOTED tokens, only the quoted ones
    are real names (this skips an f-string placeholder like ``{missing}`` that the
    traceback's source line carries alongside the resolved set). A fully unquoted
    fragment falls back to comma-split, but a lone bare identifier that looks like
    a placeholder is rejected."""
    quoted = re.findall(r"['\"]([\w .-]+?)['\"]", blob)
    raw = quoted if quoted else [t.strip() for t in blob.split(",")]
    names: list[str] = []
    lone = len(raw) == 1
    for tok in raw:
        tok = tok.strip().strip("'\"")
        if not tok:
            continue
        if lone and not quoted and tok.lower() in _PLACEHOLDER_HINTS:
            continue  # a bare ``{missing}`` placeholder, not a column
        if tok not in names:
            names.append(tok)
    return names


def _code_files(code: Path) -> list[Path]:
    return [p for p in code.rglob("*.py") if "/.venv/" not in str(p)]


def _scripts_referencing_path(code: Path, data_path: str) -> tuple[list[str], list[str]]:
    """Return (producers, consumers): scripts that WRITE vs READ ``data_path``.

    A script is a PRODUCER if it mentions the path literal (or its basename) near a
    write call (``to_csv``/``to_parquet``/``DictWriter``/``open(...,'w')``/``np.save``
    /``writeheader``/``json.dump``); a CONSUMER if it mentions it near a read call
    (``read_csv``/``read_parquet``/``DictReader``/``open(...)``/``np.load``/
    ``json.load``). A script may be both (rare). Membership is by the path literal
    OR its basename, so ``Path("results")/"metrics.csv"`` still matches ``metrics.csv``.
    """
    base = Path(data_path).name
    write_tokens = ("to_csv", "to_parquet", "to_json", "to_feather", "dictwriter",
                    "writeheader", "writerow", "np.save", "np.savez", "savetxt",
                    "json.dump", "pickle.dump", "df.to_", ".save(")
    read_tokens = ("read_csv", "read_parquet", "read_json", "read_feather",
                   "dictreader", "np.load", "json.load", "pickle.load", "load_csv",
                   "loadtxt", "pd.read", "read_table")
    producers: list[str] = []
    consumers: list[str] = []
    for p in _code_files(code):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if data_path not in text and base not in text:
            continue
        rel = str(p.relative_to(code.parent))
        low = text.lower()
        # An open(...) with a write mode anywhere is a strong producer signal.
        writes = any(t in low for t in write_tokens) or bool(
            re.search(r"open\s*\([^)]*['\"][wa]\b", low)
        )
        reads = any(t in low for t in read_tokens) or bool(
            re.search(r"open\s*\([^)]*['\"]r?b?['\"]?\s*\)", low)
        )
        if writes:
            producers.append(rel)
        if reads or not writes:  # a plain mention with no write is treated as a read
            consumers.append(rel)
    return producers, consumers


def _read_actual_schema(data_path_abs: Path) -> list[str] | None:
    """Read the REAL schema of an existing artifact: CSV/TSV header row, parquet/
    feather columns (via pandas if available, else skip), or JSON top-level keys.
    Returns ``None`` if the file is absent or unreadable as a schema."""
    if not data_path_abs.is_file():
        return None
    suf = data_path_abs.suffix.lower()
    try:
        if suf in (".csv", ".tsv"):
            delim = "\t" if suf == ".tsv" else ","
            with data_path_abs.open(encoding="utf-8", errors="replace", newline="") as fh:
                row = next(csv.reader(fh, delimiter=delim), None)
            return [c.strip() for c in row] if row else []
        if suf == ".json":
            data = json.loads(data_path_abs.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict):
                return list(data.keys())
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return list(data[0].keys())
            return []
        if suf in (".parquet", ".feather"):
            try:
                import pandas as pd  # optional dependency
            except ImportError:
                return None
            reader = pd.read_parquet if suf == ".parquet" else pd.read_feather
            return list(reader(data_path_abs).columns)
    except (OSError, ValueError, StopIteration, csv.Error):
        return None
    return None


def find_data_contract_issues(project_dir: Path, failures: list[str]) -> list[DataContractIssue]:
    """Detect cross-script DATA-schema mismatches in the run-book ``failures``.

    Returns one issue per data file, carrying the required columns/keys (union over
    all failures touching that file), the file's REAL on-disk schema, and the
    producer/consumer scripts. A missing-intermediate-file error yields an issue
    flagged ``missing_file`` whose producers are the scripts that should write it.
    """
    code = Path(project_dir) / "code"
    if not code.is_dir():
        return []
    by_file: dict[str, DataContractIssue] = {}

    def issue_for(data_path: str) -> DataContractIssue:
        data_path = data_path.lstrip("./")
        iss = by_file.get(data_path)
        if iss is None:
            iss = DataContractIssue(data_file=data_path)
            by_file[data_path] = iss
        return iss

    # Process each failure block independently so a missing-columns error is
    # attributed to the data path the SAME failing consumer reads (the message
    # itself names no path).
    for block in failures:
        # 1) Missing intermediate file (explicit path in the message).
        for pat in _MISSING_FILE_PATTERNS:
            for m in pat.finditer(block):
                path = m.group(1)
                if not re.search(rf"\.(?:{_DATA_EXTS})$", path, re.IGNORECASE):
                    continue
                iss = issue_for(path)
                iss.missing_file = True

        # 2) Missing columns / KeyError → required names; attribute to the data
        #    file this consumer reads.
        required: list[str] = []
        for pat in _MISSING_COLS_PATTERNS:
            for m in pat.finditer(block):
                required += _parse_names(m.group(1))
        for m in _KEYERROR_PATTERN.finditer(block):
            required.append(m.group(1).strip())
        if required:
            data_path = _attribute_data_file(code, block)
            if data_path:
                iss = issue_for(data_path)
                for r in required:
                    if r not in iss.required:
                        iss.required.append(r)

    # Resolve producers/consumers + real schema for every file we found.
    out: list[DataContractIssue] = []
    for data_path, iss in by_file.items():
        iss.producers, iss.consumers = _scripts_referencing_path(code, data_path)
        iss.actual = _read_actual_schema(project_dir / data_path)
        out.append(iss)
    # Stable ordering: files with a known required-column mismatch first.
    out.sort(key=lambda i: (not i.required, i.data_file))
    return out


def _attribute_data_file(code: Path, block: str) -> str | None:
    """Find the data file a missing-columns/KeyError failure is about.

    The error names no path, so: (1) if the block mentions a data-file token
    directly, use it; else (2) take the consumer source file from the traceback
    and grep IT for the data-file literal it reads."""
    # (1) explicit path token in the block (e.g. a path printed in the message).
    tokens = _DATA_PATH_TOKEN.findall(block)
    if tokens:
        return tokens[0].lstrip("./")
    # (2) the failing consumer's source file → the path literal inside it.
    src_files = _TRACEBACK_FILE.findall(block)
    for src in reversed(src_files):  # innermost frame first
        # Map the absolute traceback path back to a file under THIS code/ tree.
        name = Path(src).name
        for p in _code_files(code):
            if p.name != name:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lits = _DATA_PATH_TOKEN.findall(text)
            if lits:
                return lits[0].lstrip("./")
    return None


# ---------------------------------------------------------------------------
# Cumulative data-contract ledger (anti-thrash) — mirrors shared_contract.
#
# A data file reconciled in round N can regress in round N+2 because each round's
# feedback shows only THAT round's failures. Persisting every data file ever
# flagged and re-rendering the COMPLETE set each round (with the schema re-read
# from the live file) keeps every contract in front of the implementer. A file
# whose producers AND consumers have all vanished is dropped.
# ---------------------------------------------------------------------------
def _ledger_path(mem_dir: Path) -> Path:
    return Path(mem_dir) / _LEDGER_FILENAME


def _load_ledger(mem_dir: Path) -> dict[str, list[str]]:
    try:
        data = json.loads(_ledger_path(mem_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict[str, list[str]] = {}
    for entry in data if isinstance(data, list) else []:
        if isinstance(entry, dict) and entry.get("data_file"):
            out[entry["data_file"]] = list(entry.get("required") or [])
    return out


def _save_ledger(mem_dir: Path, files: dict[str, list[str]]) -> None:
    payload = [
        {"data_file": f, "required": req} for f, req in sorted(files.items())
    ]
    try:
        p = _ledger_path(mem_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def accumulate_data_contract_issues(
    mem_dir: Path, project_dir: Path, current: list[DataContractIssue]
) -> list[DataContractIssue]:
    """Merge ``current`` into the persistent ledger and return the FULL set.

    Every data file ever flagged is remembered along with the union of required
    columns. The returned issues carry producers/consumers + the schema re-read
    from the CURRENT file. A file with no producers AND no consumers in the live
    code is dropped (the implementer legitimately removed it)."""
    files = _load_ledger(mem_dir)
    for iss in current:
        merged = files.setdefault(iss.data_file, [])
        for r in iss.required:
            if r not in merged:
                merged.append(r)
    _save_ledger(mem_dir, files)

    code = Path(project_dir) / "code"
    out: list[DataContractIssue] = []
    for data_path, required in sorted(files.items()):
        producers, consumers = _scripts_referencing_path(code, data_path)
        if not producers and not consumers:
            continue
        actual = _read_actual_schema(Path(project_dir) / data_path)
        out.append(
            DataContractIssue(
                data_file=data_path, required=list(required), actual=actual,
                producers=producers, consumers=consumers,
                missing_file=(actual is None and not required),
            )
        )
    out.sort(key=lambda i: (not i.required, i.data_file))
    return out


def reopen_targets(issues: list[DataContractIssue]) -> set[str]:
    """Re-open targets: the producer (and consumer) scripts to re-implement.

    The producer is preferred (one canonical schema, written at the source), but
    consumers are included too because the chosen fix may legitimately adjust a
    reader. Returns both repo-relative paths and bare stems (matching how
    ``shared_contract.defining_files`` and ``_reopen_failing_tasks`` match)."""
    out: set[str] = set()
    for iss in issues:
        for rel in (*iss.producers, *iss.consumers):
            out.add(rel)
            out.add(Path(rel).stem)
    return out


def render_data_contract_feedback(issues: list[DataContractIssue]) -> str:
    """Render the implementer feedback grounding the fix in the REAL artifacts."""
    actionable = [i for i in issues if i.required or i.missing_file]
    if not actionable:
        return ""
    lines = [
        "",
        "## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read",
        "",
        "One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that "
        "exchange a file: a CONSUMER requires column/key names (or a file) that the "
        "PRODUCER did not write. The traceback you saw shows only the CONSUMER's "
        "EXPECTATION — never the producer's ACTUAL output — which is why this keeps "
        "failing. Below is the REAL schema each producer wrote on disk (read from "
        "the actual file) versus what the consumers require. Pick ONE canonical "
        "schema and make the **PRODUCER** write exactly the columns/keys the "
        "consumers read (preferred when one producer feeds several consumers), "
        "editing the producer IN PLACE. Do NOT fake or stub the data.",
        "",
        "**This list is CUMULATIVE across every fix round** — keep satisfying a "
        "contract you already fixed while you fix the rest; do not drop a column "
        "merely because it is absent from this round's traceback.",
    ]

    for iss in actionable:
        lines += ["", f"### `{iss.data_file}`"]
        if iss.missing_file and iss.actual is None:
            # The file was never produced (cascade root): point at its producer.
            if iss.producers:
                prod = ", ".join(f"`{p}`" for p in iss.producers)
                lines += [
                    "",
                    f"This file is MISSING — it was never written, so every "
                    f"consumer of it fails as a CASCADE. Its producer is {prod}; "
                    "that script failed earlier this run (fix ITS failure first) or "
                    "is not in the run-book. Make the producer run cleanly and WRITE "
                    f"`{iss.data_file}`; do NOT edit the cascade-victim consumers in "
                    "isolation — they clear once the producer writes the file.",
                ]
            else:
                lines += [
                    "",
                    f"This file is MISSING and NO script writes it. Add a producer "
                    f"that writes `{iss.data_file}` (or correct the path a consumer "
                    "reads to an existing produced file).",
                ]
            if iss.consumers:
                lines.append(
                    "Consumers waiting on it: "
                    + ", ".join(f"`{c}`" for c in iss.consumers) + "."
                )
            continue

        actual_str = (
            "[" + ", ".join(iss.actual) + "]" if iss.actual is not None
            else "(file not on disk this run)"
        )
        required_str = "[" + ", ".join(iss.required) + "]"
        lines += [
            "",
            f"- ACTUAL columns/keys the producer wrote: `{actual_str}`",
            f"- REQUIRED by the consumer(s): `{required_str}`",
        ]
        if iss.actual is not None:
            missing = [r for r in iss.required if r not in iss.actual]
            if missing:
                lines.append(f"- MISSING (required but not written): `{missing}`")
            renames = iss.rename_map()
            if renames:
                arrows = ", ".join(f"{a} -> {b}" for a, b in sorted(renames.items()))
                lines.append(
                    f"- LIKELY just a rename in the PRODUCER: {arrows}. Rename these "
                    "columns where the producer writes them (keep every other "
                    "existing column) so each required name above is present."
                )
        if iss.producers:
            lines.append("- PRODUCER(s) to edit: " + ", ".join(f"`{p}`" for p in iss.producers))
        if iss.consumers:
            lines.append("- CONSUMER(s) that read it: " + ", ".join(f"`{c}`" for c in iss.consumers))
        lines.append(
            f"  → Edit the producer so every required name {required_str} is in "
            f"`{iss.data_file}`'s header (renaming, not dropping, the columns it "
            "already writes); do not change the consumers (they already agree)."
        )
    return "\n".join(lines)


__all__ = [
    "DataContractIssue",
    "accumulate_data_contract_issues",
    "find_data_contract_issues",
    "render_data_contract_feedback",
    "reopen_targets",
]
