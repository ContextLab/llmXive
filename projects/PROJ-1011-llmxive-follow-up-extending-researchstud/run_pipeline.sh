#!/usr/bin/env bash
# Orchestration script for the llmXive follow-up pipeline.
#
# Usage:
#   ./run_pipeline.sh --stage all           # real end-to-end execution
#   ./run_pipeline.sh --stage all --dry-run # health-check only, no external calls
#
set -euo pipefail
cd "$(dirname "$0")"

STAGE="all"
DRY_RUN=false

usage() {
    cat <<'EOF'
Usage: ./run_pipeline.sh [--stage STAGE] [--dry-run]

Stages:
  all   Run the full pipeline (acquisition -> mapping -> generation ->
        evaluation -> statistical analysis)

Options:
  --dry-run  Run only the local health check (no network, no LLM calls).
  -h, --help Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --stage)
            STAGE="${2:-}"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ "$STAGE" != "all" ]]; then
    echo "ERROR: unsupported stage '$STAGE' (only 'all' is supported)" >&2
    exit 2
fi

PY="${PYTHON:-python3}"

health_check() {
    echo "[health-check] Python interpreter:"
    "$PY" --version
    echo "[health-check] Verifying pinned requirements manifest..."
    if [[ ! -f requirements.txt ]]; then
        echo "ERROR: requirements.txt not found" >&2
        exit 1
    fi
    if grep -Eq '^[a-zA-Z0-9_-]+[^=]*[><~]' requirements.txt; then
        echo "ERROR: requirements.txt contains unpinned (range) dependencies" >&2
        exit 1
    fi
    echo "[health-check] requirements.txt present with exact pins."
    for d in code data/raw data/processed data/results tests; do
        if [[ ! -d "$d" ]]; then
            echo "[health-check] creating missing directory: $d"
            mkdir -p "$d"
        fi
    done
    echo "[health-check] OK - dry-run complete, no external calls made."
}

if [[ "$DRY_RUN" == true ]]; then
    health_check
    exit 0
fi

# ------------------------------------------------------------------
# Full pipeline (real execution; each stage fails loudly via set -e)
# ------------------------------------------------------------------
echo "[pipeline] Stage 1/5: data acquisition"
"$PY" code/01_data_acquisition.py

echo "[pipeline] Stage 2/5: pattern mapping"
"$PY" code/02_pattern_mapping.py

echo "[pipeline] Stage 3/5: proposal generation"
"$PY" code/03_proposal_generation.py

echo "[pipeline] Stage 4/5: evaluation loader (blinding + deterministic dry-run ratings)"
"$PY" code/04_evaluation_loader.py
"$PY" code/04_evaluation_loader.py --generate-mock

echo "[pipeline] Stage 5/5: statistical analysis"
"$PY" code/05_statistical_analysis.py

echo "[pipeline] All stages completed successfully."
