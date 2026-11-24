"""
code/main.py
------------

Orchestrator for the llmXive follow-up project (feature
001-policy-compression-tradeoff).

Implements the full pipeline in one command:
    generate -> execute (full and compressed) -> analyze

Usage:
    python code/main.py --generate --compress --analyze
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
DEFAULT_DEPTHS = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

_ARRAY_PROP_HINTS = ("workflows", "logs", "executions", "records", "results")

def _fail(message: str) -> None:
    print(f"ERROR [main]: {message}", file=sys.stderr, flush=True)
    sys.exit(1)

def _run_command(cmd: List[object], description: str) -> None:
    cmd_strs = [str(c) for c in cmd]
    print(f"[main] {description}: {' '.join(cmd_strs)}", flush=True)
    result = subprocess.run(cmd_strs, cwd=str(ROOT))
    if result.returncode != 0:
        _fail(f"{description} failed with exit code {result.returncode}")

def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        _fail(f"{description} did not produce output file at {path}")
    if path.stat().st_size == 0:
        _fail(f"{description} produced an EMPTY output file at {path}")

def _load_schema(schema_path: Path, description: str) -> Dict[str, Any]:
    if not schema_path.is_file():
        _fail(f"schema contract {schema_path} is missing for {description}")
    try:
        return yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        _fail(f"could not parse schema {schema_path}: {exc}")

def _adapt_schema_to_instance(schema: Dict[str, Any], data: Any, description: str) -> Dict[str, Any]:
    if not (isinstance(data, list) and schema.get("type") == "object"):
        return schema
    props = schema.get("properties") or {}
    chosen = None
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
        _fail(f"contract for {description} is object-typed but exposes no array property")
    prop = props[chosen]
    adapted = {"type": "array", "items": prop.get("items", {})}
    for key in ("minItems", "maxItems", "uniqueItems"):
        if key in prop: adapted[key] = prop[key]
    return adapted

def validate_against_schema(data_path: Path, schema_path: Path, description: str) -> None:
    schema = _load_schema(schema_path, description)
    try:
        with open(data_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"could not read/parse {data_path}: {exc}")
    schema = _adapt_schema_to_instance(schema, data, description)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        _fail(f"schema validation FAILED for {description}: {exc.message}")
    print(f"[main] schema validation PASSED for {description}", flush=True)

def step_generate(args: argparse.Namespace) -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    generator_script = CODE_DIR / "generators" / "synthetic_workflow.py"
    _run_command([sys.executable, generator_script, "--count", str(args.n_workflows), "--seed", str(args.seed), "--output", WORKFLOWS_PATH], "Workflow generation")
    _require_file(WORKFLOWS_PATH, "Workflow generation")
    validate_against_schema(WORKFLOWS_PATH, WORKFLOW_SCHEMA, "generated workflows")

def step_compress(args: argparse.Namespace) -> None:
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    full_engine = CODE_DIR / "engines" / "full_context.py"
    _run_command([sys.executable, full_engine, "--workflow", WORKFLOWS_PATH, "--output", FULL_LOGS_PATH], "Full-context execution")
    _require_file(FULL_LOGS_PATH, "Full-context execution")
    validate_against_schema(FULL_LOGS_PATH, EXECUTION_LOG_SCHEMA, "full-context logs")

    compressed_engine = CODE_DIR / "engines" / "compressed_context.py"
    depth_tokens = [str(d) for d in args.depths]
    _run_command([sys.executable, compressed_engine, "--workflow", WORKFLOWS_PATH, "--depths", *depth_tokens, "--output", COMPRESSED_LOGS_PATH], "Compressed-context execution")
    _require_file(COMPRESSED_LOGS_PATH, "Compressed-context execution")
    validate_against_schema(COMPRESSED_LOGS_PATH, EXECUTION_LOG_SCHEMA, "compressed-context logs")

def step_analyze() -> None:
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)
    if str(CODE_DIR) not in sys.path:
        sys.path.insert(0, str(CODE_DIR))
    try:
        from analysis.tradeoff_model import main as run_analysis_pipeline
        run_analysis_pipeline()
    except ImportError as exc:
        _fail(f"could not import the analysis pipeline: {exc}")
    _require_file(TRADEOFF_CSV_PATH, "Analysis - CSV")
    _require_file(THRESHOLD_REPORT_PATH, "Analysis - Threshold JSON")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python code/main.py")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--n-workflows", type=int, default=DEFAULT_N_WORKFLOWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--depths", type=int, nargs="+", default=DEFAULT_DEPTHS)
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    os.chdir(ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not any([args.generate, args.compress, args.analyze]):
        parser.print_help()
        return 0
    if args.generate: step_generate(args)
    if args.compress: step_compress(args)
    if args.analyze: step_analyze()
    print("[main] Pipeline finished successfully.", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())