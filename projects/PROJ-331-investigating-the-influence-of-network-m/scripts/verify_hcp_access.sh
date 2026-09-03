#!/bin/bash
#
# verify_hcp_access.sh
# Pre-validates connectivity to the HCP S3 bucket and generates a
# `data/raw/.access_verified` flag before the main pipeline runs.
#
# Purpose: Reduce CI timeout risks by failing fast if the HCP data source
# is unreachable or misconfigured.
#
# Usage:
#   ./scripts/verify_hcp_access.sh
#
# Exit codes:
#   0 - Success: Connectivity verified, flag file created.
#   1 - Failure: Connectivity check failed (no flag file created).
#

set -euo pipefail

# Configuration
# The HCP S3 bucket for anonymous access (Open Access)
HCP_BUCKET="hcp-openaccess"
# A known, small file to test connectivity. 
# Using a standard HCP structural file path pattern as a probe.
# We target a specific subject's structural file to ensure the path exists.
# Subject 100307 is a common test subject in HCP.
PROBE_PATH="HCP1200/100307/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_hp2000_clean.nii.gz"
CHECKSUM_FILE="data/raw/.checksums.json"
FLAG_FILE="data/raw/.access_verified"
LOG_FILE="data/logs/pipeline.log"

# Ensure log directory exists
mkdir -p data/logs
mkdir -p data/raw

# Function to log messages
log_msg() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log_msg "Starting HCP S3 connectivity verification..."

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    log_msg "ERROR: AWS CLI not found. Please install it to verify S3 access."
    exit 1
fi

# Check if the checksum file exists (indicating data configuration)
# If it doesn't exist, we assume we are in a fresh setup or the config is missing.
# We proceed with the connectivity check regardless, but note the missing config.
if [ ! -f "$CHECKSUM_FILE" ]; then
    log_msg "WARNING: $CHECKSUM_FILE not found. Proceeding with raw connectivity check."
fi

# Perform the connectivity check
# We attempt to list the specific object to verify access without downloading the full file.
# --no-sign-request is used for anonymous access to the public HCP bucket.
log_msg "Attempting to verify access to HCP S3 bucket: s3://$HCP_BUCKET/$PROBE_PATH"

if aws s3 ls "s3://$HCP_BUCKET/$PROBE_PATH" --no-sign-request > /dev/null 2>&1; then
    log_msg "SUCCESS: Connected to HCP S3 bucket and verified object existence."
    
    # Create the flag file
    # The content includes a timestamp and the verified bucket name for provenance.
    echo "VERIFIED" > "$FLAG_FILE"
    echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$FLAG_FILE"
    echo "bucket=$HCP_BUCKET" >> "$FLAG_FILE"
    echo "probe=$PROBE_PATH" >> "$FLAG_FILE"
    
    log_msg "Flag file created: $FLAG_FILE"
    log_msg "HCP connectivity verified. Pipeline can proceed."
    exit 0
else
    log_msg "ERROR: Failed to connect to HCP S3 bucket or object not found."
    log_msg "Please check your network connection and the HCP bucket configuration."
    exit 1
fi
