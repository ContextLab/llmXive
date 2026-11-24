#!/usr/bin/env bash
set -e
# Ensure required directories exist
python -c "import code.analysis.stats as stats; stats.ensure_dirs()"
# Run the baseline metrics computation
python -m code.analysis.stats --baseline-metrics