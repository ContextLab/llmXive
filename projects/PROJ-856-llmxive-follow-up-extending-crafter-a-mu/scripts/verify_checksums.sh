#!/usr/bin/env bash
#
# verify_checksums.sh
#
# Recomputes SHA‑256 checksums for every file listed in
# data/checksums.txt, writes a verification log to
# data/env_evidence/checksum_verify.log, and exits with status 0
# only if all files match their recorded hashes.
#
set -euo pipefail

# Determine project root (assumed to be the directory containing this script's parent)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${PROJECT_ROOT}/data"
LOG_FILE="${PROJECT_ROOT}/data/env_evidence/checksum_verify.log"

# Ensure the log directory exists
mkdir -p "$(dirname "${LOG_FILE}")"

# Initialise log
echo "Checksum verification started at $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "${LOG_FILE}"
echo "------------------------------------------------------------" >> "${LOG_FILE}"

FAIL=0

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip empty lines
  [[ -z "$line" ]] && continue

  # Expected format: "<checksum>  <relative_path>"
  expected_checksum=$(echo "$line" | awk '{print $1}')
  relative_path=$(echo "$line" | awk '{print $2}')

  file_path="${DATA_ROOT}/${relative_path}"

  if [[ ! -f "${file_path}" ]]; then
    echo "${relative_path}: MISSING" >> "${LOG_FILE}"
    FAIL=1
    continue
  fi

  # Compute actual SHA‑256 using a small Python snippet (portable, no external tools)
  actual_checksum=$(python - <<'PYEOF'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
hasher = hashlib.sha256()
with path.open('rb') as f:
    for chunk in iter(lambda: f.read(8192), b''):
  hasher.update(chunk)
print(hasher.hexdigest())
PYEOF
"${file_path}"
  )

  if [[ "${actual_checksum}" == "${expected_checksum}" ]]; then
    echo "${relative_path}: OK" >> "${LOG_FILE}"
  else
    echo "${relative_path}: FAIL (expected ${expected_checksum} got ${actual_checksum})" >> "${LOG_FILE}"
    FAIL=1
  fi
done < "${DATA_ROOT}/checksums.txt"

echo "------------------------------------------------------------" >> "${LOG_FILE}"
if [[ ${FAIL} -ne 0 ]]; then
  echo "Checksum verification completed: SOME FILES DID NOT MATCH" >> "${LOG_FILE}"
  exit 1
else
  echo "Checksum verification completed: ALL FILES MATCH" >> "${LOG_FILE}"
  exit 0
fi