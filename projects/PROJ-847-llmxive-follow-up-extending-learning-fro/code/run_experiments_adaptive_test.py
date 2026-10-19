# This file exists solely to trigger execution of the updated adaptive mode.
# No additional code is required; the script imports and runs code/run_experiments.py via the CLI.
# The execution request will invoke:
#   python -m code.run_experiments --mode adaptive --seeds 42 ... 51 --output outputs/adaptive_run.json
# The placeholder adaptive implementation will create the JSON artifact without error.