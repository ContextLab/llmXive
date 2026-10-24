#!/usr/bin/env bash
set -e
# Wrapper script to run the R dependency verification script.
# This ensures the platform's executor (which supports .sh) can invoke the R script.
Rscript "$(dirname "$0")/verify_requirements.R"
# Exit status of Rscript will be propagated automatically.