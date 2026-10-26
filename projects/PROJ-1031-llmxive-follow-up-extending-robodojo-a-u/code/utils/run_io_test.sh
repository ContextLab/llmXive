#!/usr/bin/env bash
set -e
# Run the IO utility in test mode to ensure it can stream at least one record.
python -m code.utils.io --test
# Verify full checksum validation (will succeed if the dataset is reachable).
python -m code.utils.io --verify-checksums
echo "IO script verification completed successfully."