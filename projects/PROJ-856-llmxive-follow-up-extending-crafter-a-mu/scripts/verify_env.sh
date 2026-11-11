#!/usr/bin/env bash
# ------------------------------------------------------------
# verify_env.sh
#
# Installs the exact dependencies pinned in ``requirements.txt``
# and writes the full pip output to ``data/env_evidence/pip_install.log``.
# ------------------------------------------------------------

set -e  # Exit immediately on any error.

# Ensure the output directory exists.
mkdir -p data/env_evidence

# Install the requirements, capturing *both* stdout and stderr.
# The output is written to the log file; tee is not required because
# the CI runner captures the script's exit status.
pip install -r requirements.txt > data/env_evidence/pip_install.log 2>&1
