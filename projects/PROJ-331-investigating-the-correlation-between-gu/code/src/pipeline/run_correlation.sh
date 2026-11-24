#!/usr/bin/env bash
set -e
# Display the contents of the pipeline entry point and correlation module
echo "=== __main__.py ==="
cat "$(python - <<EOF
import importlib.util, pathlib, sys
spec = importlib.util.find_spec('src.pipeline.__main__')
if spec is None:
    sys.exit(1)
print(pathlib.Path(spec.origin))
EOF
)"
echo "=== correlation.py ==="
cat "$(python - <<EOF
import importlib.util, pathlib, sys
spec = importlib.util.find_spec('src.pipeline.correlation')
if spec is None:
    sys.exit(1)
print(pathlib.Path(spec.origin))
EOF
)"
# Run the full pipeline to generate the required correlation CSV
echo "Running full pipeline to produce taxa_correlations.csv ..."
python -m code.src.pipeline \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000
echo "=== Generated taxa_correlations.csv ==="
head -n 10 "$(python - <<EOF
import pathlib, importlib.util, sys
spec = importlib.util.find_spec('src.pipeline.correlation')
if spec is None:
    sys.exit(1)
# The correlation module writes to data/results/taxa_correlations.csv via llmxive_toolkit.paths
from llmxive_toolkit import paths
print(paths.results('taxa_correlations.csv'))
EOF
)"