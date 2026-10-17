"""
code/main.py
------------

Orchestrator for the llmXive follow‑up project (feature
001‑policy‑compression‑tradeoff).

Implements the full pipeline in one command:

    generate → execute (full context + compressed context) → analyze

The orchestrator reuses existing modules under ``code/`` (the deterministic
workflow generator, the full/compressed execution engines, and the
trade‑off analysis pipeline in ``code/analysis/tradeoff_model.py``).

The implementation follows a *detect‑and‑skip* strategy:

* If the required artifact already exists (e.g. ``data/raw/workflows.json``),
  the step validates the file against its contract and proceeds.
* If the artifact is missing, the step attempts to invoke the corresponding
  script **only if the script exists**; otherwise it aborts with a clear
  error message.  This avoids hard‑coded paths to non‑existent files while
  still ensuring that a complete run produces all declared outputs.

The orchestrator fails loudly (non‑zero exit) on any subprocess failure,
missing/empty output artifact, or schema‑validation error.  Token counting
throughout the pipeline uses the ``cl100k_base`` tokenizer (FR‑009).

Usage:
    python code/main.py --generate --compress --analyze
    python code/main.py --generate --compress --analyze --n-workflows 20
    python code/main.py --generate --seed 42 --n-workflows 500
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

from llmxive_toolkit import paths

# ---------------------------------------------------------------------------
# Project locations (resolved relative to the project root, never the CWD)
# ---------------------------------------------------------------------------
ROOT = paths.root
CODE_DIR = ROOT / "code"
CONTRACTS_DIR = ROOT / "contracts"

DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
DATA_RESULTS = ROOT / "data" / "results"

WORKFLOWS_PATH = DATA_RAW / "workflows.json"
FULL_LOGS_PATH = DATA_PROC / "full_context_logs.json"
COMPRESSED_LOGS_PATH = DATA_PROC / "compressed_context_logs.json"
TRADEOFF_CSV_PATH = DATA_RESULTS / "tradeoff_curve.csv"
THRESHOLD_REPORT_PATH = DATA_RESULTS / "threshold_report.json"

WORKFLOW_SCHEMA = CONTRACTS_DIR / "workflow.schema.yaml"
EXECUTION_LOG_SCHEMA = CONTRACTS_DIR / "execution_log.schema.yaml"

DEFAULT_SEED = 42
DEFAULT_N_WORKFLOWS = 500
# Compression depths used by the compressed‑context engine.
DEFAULT_DEPTHS = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

# Preferred property names when looking for the record‑array property
# inside an object‑typed contract.
_ARRAY_PROP_HINTS = ("workflows", "logs", "executions", "records", "results")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _fail(message: str) -> None:
    """Print an error and abort the pipeline loudly (exit code 1)."""
    print(f"ERROR [main]: {message}", file=sys.stderr, flush=True)
    sys.exit(1)

def _run_command(cmd: List[object], description: str) -> None:
    """Run a pipeline step as a subprocess; fail loudly on error."""
    cmd_strs = [str(c) for c in cmd]
    print(f"[main] {description}: {' '.join(cmd_strs)}", flush=True)
    result = subprocess.run(cmd_strs, cwd=str(ROOT))
    if result.returncode != 0:
        _fail(
            f"{description} failed with exit code {result.returncode} "
            f"(command: {' '.join(cmd_strs)})"
        )

def _require_file(path: Path, description: str) -> None:
    """Assert that a pipeline artifact exists and is non‑empty."""
    if not path.is_file():
        _fail(f"{description} did not produce the required output file at {path}")
    if path.stat().st_size == 0:
        _fail(f"{description} produced an EMPTY output file at {path}")

def _load_schema(schema_path: Path, description: str) -> Dict[str, Any]:
    """Load and parse a YAML JSON‑Schema contract; fail loudly on error."""
    if not schema_path.is_file():
        _fail(f"schema contract {schema_path} is missing; cannot validate {description}")
    try:
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        _fail(f"could not parse schema {schema_path}: {exc}")
    if not isinstance(schema, dict):
        _fail(f"schema {schema_path} did not parse to a JSON object")
    return schema

def _adapt_schema_to_instance(
    schema: Dict[str, Any], data: Any, description: str
) -> Dict[str, Any]:
    """
    Align an object‑typed contract with an array‑typed artifact.

    The generator/engines write top‑level JSON arrays of records. If
    the contract instead defines a top‑level object that wraps the
    record array in a property (e.g. ``workflows``), build an array
    schema from that property (``items`` plus ``minItems`` /
    ``maxItems`` / ``uniqueItems``) so every record is validated
    against the real contract subschema. Any other shape mismatch
    fails loudly.
    """
    if not (isinstance(data, list) and schema.get("type") == "object"):
        return schema
    props = schema.get("properties") or {}
    if not isinstance(props, dict):
        _fail(f"contract for {description} has a malformed 'properties' block")
    chosen: Optional[str] = None
    for hint in _ARRAY_PROP_HINTS:
        prop = props.get(hint)
        if isinstance(prop, dict) and prop.get("type") == "array":
            chosen = hint
            break
    if chosen is None:
        for name, prop in props.items():
            if isinstance(prop, dict) and prop.get("type") == "array":
                chosen = name
                break
    if chosen is None:
        _fail(
            f"contract for {description} is object‑typed but exposes no "
            f"array property to validate the array artifact against "
            f"(properties: {sorted(props)})"
        )
    prop = props[chosen]
    adapted: Dict[str, Any] = {"type": "array", "items": prop.get("items", {})}
    for key in ("minItems", "maxItems", "uniqueItems"):
        if key in prop:
            adapted[key] = prop[key]
    print(
        f"[main] note: array artifact for {description} validated "
        f"element‑wise against contract property '{chosen}'",
        flush=True,
    )
    return adapted

def validate_against_schema(data_path: Path, schema_path: Path, description: str) -> None:
    """
    Validate a JSON artifact against a YAML JSON‑Schema contract.

    Fails loudly (exit 1) if the schema file is missing, the data does
    not parse, or the data violates the schema. No silent fallbacks.
    """
    schema = _load_schema(schema_path, description)
    try:
        with open(data_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"could not read/parse {data_path} for {description}: {exc}")
    schema = _adapt_schema_to_instance(schema, data, description)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        _fail(
            f"schema validation FAILED for {description} "
            f"({data_path} vs {schema_path}): {exc.message} "
            f"at path {list(exc.absolute_path)}"
        )
    except jsonschema.SchemaError as exc:
        _fail(f"schema itself is invalid ({schema_path}): {exc.message}")
    print(f"[main] schema validation PASSED for {description}: {data_path}", flush=True)

# ---------------------------------------------------------------------------
# Pipeline steps (generate → compress → analyze)
# ---------------------------------------------------------------------------
def step_generate(args: argparse.Namespace) -> None:
    """Generate the deterministic synthetic workflow set (FR‑001)."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    # If the workflow file already exists, just validate it.
    if WORKFLOWS_PATH.is_file():
        _require_file(WORKFLOWS_PATH, "Workflow generation (pre‑existing)")
        validate_against_schema(
            WORKFLOWS_PATH, WORKFLOW_SCHEMA, "generated workflows"
        )
        print("[main] Skipping generation – workflows.json already present.", flush=True)
        return

    # Path to the generator script.
    generator_script = CODE_DIR / "generators" / "synthetic_workflow.py"
    if not generator_script.is_file():
        _fail(
            f"Generator script not found at {generator_script}. "
            "Cannot generate workflows and no pre‑existing file is available."
        )
    _run_command(
        [
            sys.executable,
            generator_script,
            "--count",
            str(args.n_workflows),
            "--seed",
            str(args.seed),
            "--output",
            WORKFLOWS_PATH,
        ],
        "Workflow generation",
    )
    _require_file(WORKFLOWS_PATH, "Workflow generation")
    validate_against_schema(
        WORKFLOWS_PATH, WORKFLOW_SCHEMA, "generated workflows"
    )

def step_compress(args: argparse.Namespace) -> None:
    """Execute full‑context baseline and compressed‑context variants."""
    if not WORKFLOWS_PATH.is_file():
        _fail(
            f"{WORKFLOWS_PATH} is missing; run with --generate before --compress"
        )
    DATA_PROC.mkdir(parents=True, exist_ok=True)

    # ---------- Full‑context ----------
    if FULL_LOGS_PATH.is_file():
        _require_file(FULL_LOGS_PATH, "Full‑context execution (pre‑existing)")
        validate_against_schema(
            FULL_LOGS_PATH, EXECUTION_LOG_SCHEMA, "full‑context execution logs"
        )
        print("[main] Skipping full‑context execution – file already present.", flush=True)
    else:
        full_engine = CODE_DIR / "engines" / "full_context.py"
        if not full_engine.is_file():
            _fail(f"Full‑context engine script not found at {full_engine}")
        _run_command(
            [
                sys.executable,
                full_engine,
                "--workflow",
                WORKFLOWS_PATH,
                "--output",
                FULL_LOGS_PATH,
            ],
            "Full‑context execution",
        )
        _require_file(FULL_LOGS_PATH, "Full‑context execution")
        validate_against_schema(
            FULL_LOGS_PATH, EXECUTION_LOG_SCHEMA, "full‑context execution logs"
        )

    # ---------- Compressed‑context ----------
    if COMPRESSED_LOGS_PATH.is_file():
        _require_file(COMPRESSED_LOGS_PATH, "Compressed‑context execution (pre‑existing)")
        validate_against_schema(
            COMPRESSED_LOGS_PATH,
            EXECUTION_LOG_SCHEMA,
            "compressed‑context execution logs",
        )
        print("[main] Skipping compressed‑context execution – file already present.", flush=True)
    else:
        compressed_engine = CODE_DIR / "engines" / "compressed_context.py"
        if not compressed_engine.is_file():
            _fail(f"Compressed‑context engine script not found at {compressed_engine}")
        depth_tokens: List[str] = [str(d) for d in args.depths]
        _run_command(
            [
                sys.executable,
                compressed_engine,
                "--workflow",
                WORKFLOWS_PATH,
                "--depths",
                *depth_tokens,
                "--output",
                COMPRESSED_LOGS_PATH,
            ],
            "Compressed‑context execution",
        )
        _require_file(COMPRESSED_LOGS_PATH, "Compressed‑context execution")
        validate_against_schema(
            COMPRESSED_LOGS_PATH,
            EXECUTION_LOG_SCHEMA,
            "compressed‑context execution logs",
        )

def step_analyze() -> None:
    """
    Run the statistical analysis pipeline (FR‑005, FR‑006).

    Reuses ``code/analysis/tradeoff_model.py`` (logistic trade‑off curve
    fit, safe‑operating‑zone threshold detection, VIF analysis), which
    writes ``data/results/tradeoff_curve.csv``,
    ``data/results/threshold_report.json`` and
    ``data/results/vif_report.json``.
    """
    for required in (FULL_LOGS_PATH, COMPRESSED_LOGS_PATH):
        if not required.is_file():
            _fail(
                f"{required} is missing; run with --generate --compress "
                "before --analyze"
            )
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)

    # Ensure the analysis package is importable.
    if str(CODE_DIR) not in sys.path:
        sys.path.insert(0, str(CODE_DIR))
    print("[main] Running analysis pipeline (tradeoff_model)...", flush=True)
    try:
        from analysis.tradeoff_model import main as run_analysis_pipeline
    except ImportError as exc:
        _fail(f"could not import the analysis pipeline: {exc}")
    run_analysis_pipeline()

    _require_file(TRADEOFF_CSV_PATH, "Analysis – trade‑off curve CSV")
    _require_file(THRESHOLD_REPORT_PATH, "Analysis – threshold report JSON")
    # Validate that the JSON parses and contains required keys.
    try:
        report = json.loads(THRESHOLD_REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"threshold_report.json is not valid JSON: {exc}")
    for key in ("threshold_pct", "ci_lower", "ci_upper"):
        if key not in report:
            _fail(f"threshold_report.json is missing required key '{key}'")
    print("[main] Analysis complete. Artifacts written to data/results/", flush=True)

# ---------------------------------------------------------------------------
# CLI construction
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python code/main.py",
        description=(
            "llmXive Foundation Protocol simulation orchestrator: "
            "generate synthetic workflows, execute them under full and "
            "compressed context regimes, and analyze the "
            "context‑reduction / policy‑violation trade‑off. "
            "All steps are deterministic (default seed 42) and CPU‑only."
        ),
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help=(
            "Generate the deterministic synthetic workflow set and write "
            "data/raw/workflows.json (validated against "
            "contracts/workflow.schema.yaml)."
        ),
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help=(
            "Execute the full‑context baseline and the compressed‑context "
            "variants, writing data/processed/full_context_logs.json and "
            "data/processed/compressed_context_logs.json (validated "
            "against contracts/execution_log.schema.yaml)."
        ),
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help=(
            "Run the statistical analysis, writing data/results/"
            "tradeoff_curve.csv, threshold_report.json and vif_report.json."
        ),
    )
    parser.add_argument(
        "--n-workflows",
        type=int,
        default=DEFAULT_N_WORKFLOWS,
        help=(
            f"Number of synthetic workflows to generate "
            f"(default: {DEFAULT_N_WORKFLOWS})."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for deterministic generation (default: {DEFAULT_SEED}).",
    )
    parser.add_argument(
        "--depths",
        type=int,
        nargs="+",
        default=DEFAULT_DEPTHS,
        help=(
            "Compression traversal depths for the compressed‑context "
            f"engine (default: {' '.join(str(d) for d in DEFAULT_DEPTHS)})."
        ),
    )
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Entry point. Returns 0 on success; exits non‑zero on any failure."""
    # Anchor the working directory at the project root for all subprocesses.
    os.chdir(ROOT)

    parser = build_parser()
    args = parser.parse_args(argv)

    # If no actionable flags are supplied, show help and exit cleanly.
    if not any([args.generate, args.compress, args.analyze]):
        parser.print_help()
        return 0

    if args.generate:
        step_generate(args)
    if args.compress:
        step_compress(args)
    if args.analyze:
        step_analyze()

    print("[main] Pipeline finished successfully.", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
