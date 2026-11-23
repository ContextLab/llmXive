#!/usr/bin/env bash
# T002-Install: install all pinned dependencies into the project venv.
# Must be run from the repository root with the project venv active
# (the runner puts the venv on PATH).
set -e
set -o pipefail

echo "=== T002-Install: installing pinned dependencies ==="
python --version
pip --version

echo "--- Step 1: pip install -r code/requirements.txt ---"
pip install -r code/requirements.txt

echo "--- Step 2: install CPU torch wheel ---"
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

echo "--- Step 3: install CPU torch-geometric wheel ---"
pip install torch-geometric==2.4.0 --index-url https://download.pytorch.org/whl/cpu

echo "--- Verification: import critical packages ---"
python - <<'EOF'
import numpy, pandas, sklearn, yaml, rdkit, datasets, huggingface_hub
import torch, torch_geometric, pyarrow
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scikit-learn", sklearn.__version__)
print("pyyaml", yaml.__version__)
print("rdkit", rdkit.__version__)
print("datasets", datasets.__version__)
print("huggingface_hub", huggingface_hub.__version__)
print("torch", torch.__version__)
print("torch-geometric", torch_geometric.__version__)
print("pyarrow", pyarrow.__version__)
print("ALL_IMPORTS_OK")
EOF

echo "=== T002-Install completed successfully ==="