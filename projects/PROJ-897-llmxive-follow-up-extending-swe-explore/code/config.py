"""
Configuration constants and path resolution for the llmXive project.
All None values must be resolved at runtime via CLI arguments or environment variables.
"""
import os
import argparse
from pathlib import Path
from typing import Final, Dict, Any, List, Optional

# --- Project Root & Paths ---
# Assuming the script is run from the project root or code/ directory.
# We resolve relative to the script location to be robust.
_SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = _SCRIPT_DIR.parent

# Directory paths relative to PROJECT_ROOT
DIR_CODE = PROJECT_ROOT / "code"
DIR_DATA_RAW = PROJECT_ROOT / "data" / "raw"
DIR_DATA_CURATED = PROJECT_ROOT / "data" / "curated"
DIR_DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DIR_TESTS_UNIT = PROJECT_ROOT / "tests" / "unit"
DIR_TESTS_INTEGRATION = PROJECT_ROOT / "tests" / "integration"
DIR_TESTS_CONTRACT = PROJECT_ROOT / "tests" / "contract"
DIR_SPECS = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-swe-explore"
DIR_STATE = PROJECT_ROOT / "state"
DIR_PAPER = PROJECT_ROOT / "paper"
DIR_DOCS = PROJECT_ROOT / "docs"
DIR_FIGURES = DIR_DOCS / "figures"

# --- Research Constants (Resolved) ---
HARD_INSTANCE_PERCENTILE: Final[float] = 0.20  # 20% as per US-1
COVERAGE_COLUMN_NAME: Final[str] = 'initial_coverage'
SWEEP_SAMPLE_SIZE: Optional[int] = None  # [deferred] - validated by T024a
SWEEP_SEED: Final[int] = 42
DEFAULT_TURN_LIMIT: Final[int] = 3  # Hard cap for main experimental run
MIN_SYNTHETIC_ISSUES: Final[int] = 50
VALIDATION_SAMPLE_SIZE: Final[int] = 10
TIE_THRESHOLD: Final[float] = 0.50  # Concrete threshold for statistical routing (FR-006)
MAX_RUNTIME_HOURS: Final[float] = 6.0
SWEEP_STABILITY_THRESHOLD: Final[float] = 0.05  # Variance threshold for stability check (SC-006)
MODEL_PRECISION: Final[str] = '-bit'

# --- Turn Limits Configuration ---
# List of turn limits to test in sensitivity sweep
TURN_LIMITS: Final[List[int]] = [1, 2, 3, 4, 5]

# --- File Names ---
FILE_RAW_DATASET = "swe_explore_raw.jsonl"
FILE_GT_DATASET = "swe_explore_with_gt.jsonl"
FILE_COVERAGE_DATASET = "swe_explore_with_coverage.jsonl"
FILE_HARD_SUBSET = "hard_subset.jsonl"
FILE_SYNTHETIC_ISSUES = "synthetic_issues.jsonl"
FILE_SYNTHETIC_META = "synthetic_issues_meta.json"
FILE_LOCKED_SUBSET = "locked_hard_subset.jsonl"
FILE_BASELINE_ONSHOT = "baseline_onshot_logs.jsonl"
FILE_BASELINE_MULTI = "baseline_multi_logs.jsonl"
FILE_ITERATIVE_LOGS = "iterative_logs.jsonl"
FILE_SWEEP_RESULTS = "sweep_results.json"
FILE_FINAL_METRICS = "final_metrics.json"
FILE_TIE_ANALYSIS = "tie_analysis.json"
FILE_STAT_ROUTING = "statistical_routing.json"
FILE_VALIDATION_REPORT = "validation_report.md"
FILE_VALIDATION_STATUS = "validation_status.json"
FILE_HUMAN_REVIEW = "human_review_instructions.md"
FILE_FEASIBILITY_REPORT = "feasibility_report.md"
FILE_RUNTIME_LOG = "runtime_log.json"
FILE_MANIFEST = "manifest.json"

# --- CLI Argument Parser Setup ---
def _create_parser() -> argparse.ArgumentParser:
    """Creates the argument parser for CLI resolution of deferred config."""
    parser = argparse.ArgumentParser(description="llmXive Configuration and Execution")
    
    # Deferred parameters
    parser.add_argument(
        "--sweep-sample-size",
        type=int,
        default=None,
        help="Override SWEEP_SAMPLE_SIZE from config. Defaults to None if not provided."
    )
    parser.add_argument(
        "--model-precision",
        type=str,
        default=None,
        help="Override MODEL_PRECISION (e.g., '8-bit', '4-bit')."
    )
    parser.add_argument(
        "--max-runtime-hours",
        type=float,
        default=None,
        help="Override MAX_RUNTIME_HOURS."
    )
    
    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "download", "curate", "run", "sweep", "stats"],
        default="full",
        help="Execution mode."
    )
    
    # Turn limit override for main run
    parser.add_argument(
        "--turn-limit",
        type=int,
        default=None,
        help=f"Override DEFAULT_TURN_LIMIT. Defaults to {DEFAULT_TURN_LIMIT}."
    )

    return parser

def resolve_deferred_config(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Resolves deferred configuration values from CLI arguments or environment variables.
    Returns a dictionary of overrides.
    """
    if args is None:
        parser = _create_parser()
        # Check if arguments are being passed; if not, try to parse sys.argv
        # But usually this is called from main.py which has already parsed.
        # If called standalone, we parse sys.argv.
        if len(os.sys.argv) > 1:
            args = parser.parse_args()
        else:
            args = parser.parse_args([])

    overrides = {}

    # SWEEP_SAMPLE_SIZE
    if args.sweep_sample_size is not None:
        overrides['SWEEP_SAMPLE_SIZE'] = args.sweep_sample_size
    elif os.environ.get('SWEEP_SAMPLE_SIZE'):
        overrides['SWEEP_SAMPLE_SIZE'] = int(os.environ['SWEEP_SAMPLE_SIZE'])

    # MODEL_PRECISION
    if args.model_precision is not None:
        overrides['MODEL_PRECISION'] = args.model_precision
    elif os.environ.get('MODEL_PRECISION'):
        overrides['MODEL_PRECISION'] = os.environ['MODEL_PRECISION']

    # MAX_RUNTIME_HOURS
    if args.max_runtime_hours is not None:
        overrides['MAX_RUNTIME_HOURS'] = args.max_runtime_hours
    elif os.environ.get('MAX_RUNTIME_HOURS'):
        overrides['MAX_RUNTIME_HOURS'] = float(os.environ['MAX_RUNTIME_HOURS'])

    # DEFAULT_TURN_LIMIT
    if args.turn_limit is not None:
        overrides['DEFAULT_TURN_LIMIT'] = args.turn_limit
    elif os.environ.get('DEFAULT_TURN_LIMIT'):
        overrides['DEFAULT_TURN_LIMIT'] = int(os.environ['DEFAULT_TURN_LIMIT'])

    return overrides

def get_path(relative_path: Path) -> Path:
    """
    Resolves a relative path to an absolute path under PROJECT_ROOT.
    Creates the directory if it doesn't exist.
    """
    absolute_path = PROJECT_ROOT / relative_path
    absolute_path.mkdir(parents=True, exist_ok=True)
    return absolute_path

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "hard_instance_percentile": HARD_INSTANCE_PERCENTILE,
        "coverage_column_name": COVERAGE_COLUMN_NAME,
        "sweep_sample_size": SWEEP_SAMPLE_SIZE,
        "sweep_seed": SWEEP_SEED,
        "default_turn_limit": DEFAULT_TURN_LIMIT,
        "min_synthetic_issues": MIN_SYNTHETIC_ISSUES,
        "validation_sample_size": VALIDATION_SAMPLE_SIZE,
        "tie_threshold": TIE_THRESHOLD,
        "max_runtime_hours": MAX_RUNTIME_HOURS,
        "sweep_stability_threshold": SWEEP_STABILITY_THRESHOLD,
        "model_precision": MODEL_PRECISION,
        "turn_limits": TURN_LIMITS,
        "paths": {
            "data_raw": str(DIR_DATA_RAW),
            "data_curated": str(DIR_DATA_CURATED),
            "data_results": str(DIR_DATA_RESULTS),
            "specs": str(DIR_SPECS),
            "figures": str(DIR_FIGURES),
        }
    }

def ensure_directories() -> None:
    """Ensures all required project directories exist."""
    dirs = [
        DIR_CODE, DIR_DATA_RAW, DIR_DATA_CURATED, DIR_DATA_RESULTS,
        DIR_TESTS_UNIT, DIR_TESTS_INTEGRATION, DIR_TESTS_CONTRACT,
        DIR_SPECS / "contracts", DIR_STATE, DIR_PAPER, DIR_FIGURES
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Ensure directories exist on import if running as a script or main entry point
# This is safe as mkdir with exist_ok=True is idempotent.
ensure_directories()
