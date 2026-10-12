set -e
# Ensure the project root is in the python path to handle relative imports in utils/
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m code.utils.verify_logging