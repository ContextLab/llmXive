# Makefile for Project PROJ-259 - Predict Plant Disease Resistance
#
# Target:
#   quickstart - Install dependencies and verify environment.
#
# Usage:
#   make quickstart
#
# This will create a file `quickstart_output.txt` containing the
# verification banner ("OK").

.PHONY: quickstart

quickstart: requirements.txt
\t@echo "Running quickstart..."
\t@python -m pip install -r requirements.txt
\t@python -c "import scikit_learn, pandas, statsmodels; print('OK')" > quickstart_output.txt
\t@echo "Quickstart completed. Output written to quickstart_output.txt"
