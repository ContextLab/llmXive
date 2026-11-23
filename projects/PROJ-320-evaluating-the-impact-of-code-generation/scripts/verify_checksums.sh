#!/bin/bash
#
# Verify checksums of raw data files
#
# Usage: ./scripts/verify_checksums.sh
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_info() {
    echo -e "[INFO] $1"
}

main() {
    log_info "Verifying checksums for raw data files..."

    if [ ! -f "data/raw/checksums.json" ]; then
        log_error "Checksum manifest not found: data/raw/checksums.json"
        exit 1
    fi

    python3 -c "
import sys
from utils.checksum import load_checksum_manifest, verify_checksum

manifest = load_checksum_manifest('data/raw/checksums.json')
failed = []

for filepath, expected_checksum in manifest.items():
    if not verify_checksum(filepath, expected_checksum):
  failed.append(filepath)

if failed:
    print(f'Failed verification for {len(failed)} files:')
    for f in failed:
  print(f'  - {f}')
    sys.exit(1)
else:
    print(f'All {len(manifest)} files verified successfully')
"

    if [ $? -eq 0 ]; then
        log_success "All checksums verified!"
    else
        log_error "Checksum verification failed!"
        exit 1
    fi
}

main "$@"