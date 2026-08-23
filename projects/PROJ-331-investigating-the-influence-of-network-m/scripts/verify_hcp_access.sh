#!/bin/bash
# verify_hcp_access.sh
# Pre-validates connectivity to the HCP S3 bucket and generates a verification flag.
# This script must be run before the main pipeline to reduce CI timeout risks.
#
# Exit codes:
#   0 - Success: Connectivity verified, flag created.
#   1 - Failure: Connectivity check failed or prerequisite directories missing.

set -e

# Configuration
HCP_BUCKET="hcp-openaccess"
# Specific path to check for availability (a small, common file or directory listing)
# Using a known small file or directory structure to verify access quickly.
CHECK_PATH="HCP1200/700Subject"
FLAG_FILE="data/raw/.access_verified"
LOG_FILE="data/logs/pipeline.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for logging
log_message() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] VERIFY_HCP: $1"
    echo "$msg"
    # Ensure log directory exists before writing
    if [ ! -d "data/logs" ]; then
        mkdir -p "data/logs"
    fi
    echo "$msg" >> "$LOG_FILE"
}

log_message "Starting HCP S3 connectivity verification..."

# 1. Ensure prerequisite directories exist
if [ ! -d "data/raw" ]; then
    log_message "ERROR: data/raw directory does not exist. Run T001 first."
    echo -e "${RED}ERROR: data/raw directory missing.${NC}"
    exit 1
fi

# 2. Check if awscli is available
if ! command -v aws &> /dev/null; then
    log_message "ERROR: AWS CLI (aws) is not installed or not in PATH."
    echo -e "${RED}ERROR: AWS CLI not found. Please install it to verify HCP access.${NC}"
    exit 1
fi

# 3. Verify connectivity
# We attempt to list a specific directory in the bucket.
# The HCP Open Access bucket is public, so no credentials are strictly needed for listing,
# but we use the public endpoint.
log_message "Attempting to list S3 path: s3://${HCP_BUCKET}/${CHECK_PATH}..."

# Use 'ls' with no-sign-request since HCP Open Access is public.
# This avoids credential errors if the runner isn't configured with AWS keys.
if aws s3 ls "s3://${HCP_BUCKET}/${CHECK_PATH}" --no-sign-request > /dev/null 2>&1; then
    log_message "SUCCESS: Connected to HCP S3 bucket and verified path availability."
    echo -e "${GREEN}SUCCESS: HCP S3 connectivity verified.${NC}"
    
    # 4. Create the flag file
    touch "$FLAG_FILE"
    log_message "Flag file created: ${FLAG_FILE}"
    echo -e "${GREEN}Flag file created: ${FLAG_FILE}${NC}"
    
    exit 0
else
    log_message "FAILURE: Could not connect to HCP S3 bucket or path not found."
    echo -e "${RED}FAILURE: Could not verify HCP S3 access. Check network or bucket configuration.${NC}"
    exit 1
fi