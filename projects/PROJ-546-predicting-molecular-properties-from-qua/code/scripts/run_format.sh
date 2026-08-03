#!/bash
# Run formatter (black) on the codebase

set -e

echo "Running black format..."
black .

echo "Format completed."
