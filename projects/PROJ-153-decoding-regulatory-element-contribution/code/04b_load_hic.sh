#!/bin/bash
# T042: Implement code/04b_load_hic.sh
# Download and process Hi-C contact matrix from Yeast 3D Genome Atlas (GSE12345)
# Output a query-ready matrix for FR-014 validation.
#
# Note: GSE12345 is a placeholder accession used in the task description.
# The script implements the logic to fetch from a real source if available,
# or fails loudly with a clear error if the specific real accession is missing/unreachable.
#
# Requirement: The pipeline MUST abort if data is missing (FR-001).
# No synthetic data generation.

set -euo pipefail

# Configuration
MANIFEST_FILE="manifest.yaml"
HIC_OUTPUT_DIR="data/processed/hic"
HIC_OUTPUT_FILE="${HIC_OUTPUT_DIR}/yeast_hic_matrix.cool"
HIC_TEMP_DIR="${HIC_OUTPUT_DIR}/temp"

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v wget &> /dev/null; then
        missing_deps+=("wget")
    fi
    
    if ! command -v cooltools &> /dev/null; then
        # Check if cooler is installed
        if ! python -c "import cooler" &> /dev/null; then
            missing_deps+=("cooler/cooltools")
        fi
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install them before running this script."
        exit 1
    fi
}

# Verify accession from manifest
verify_manifest_accession() {
    local accession="$1"
    
    if [ ! -f "$MANIFEST_FILE" ]; then
        log_error "Manifest file '$MANIFEST_FILE' not found."
        exit 1
    fi

    # Simple check if accession exists in manifest (yaml parsing with python)
    local found
    found=$(python -c "
import yaml
import sys
with open('$MANIFEST_FILE', 'r') as f:
    data = yaml.safe_load(f)
    hic_entries = data.get('hic', [])
    for entry in hic_entries:
  if entry.get('accession') == '$accession':
      print('found')
      sys.exit(0)
    sys.exit(1)
" 2>/dev/null) || {
        log_error "Hi-C accession '$accession' not found in $MANIFEST_FILE."
        log_error "The pipeline must abort if required data is missing (FR-001)."
        exit 1
    }

    log_info "Verified Hi-C accession '$accession' in manifest."
}

# Download Hi-C data
download_hic_data() {
    local accession="$1"
    local url="$2"
    
    log_info "Downloading Hi-C data for accession $accession from $url..."
    
    mkdir -p "$HIC_TEMP_DIR"
    
    # Attempt download
    if ! wget -q --show-progress -O "${HIC_TEMP_DIR}/${accession}.cool" "$url"; then
        log_error "Failed to download Hi-C data from $url"
        log_error "The pipeline must abort if data is missing (FR-001)."
        exit 1
    fi

    if [ ! -s "${HIC_TEMP_DIR}/${accession}.cool" ]; then
        log_error "Downloaded file is empty or missing."
        log_error "The pipeline must abort if data is missing (FR-001)."
        exit 1
    fi

    log_info "Download complete: ${HIC_TEMP_DIR}/${accession}.cool"
}

# Process Hi-C data (validate and convert if needed)
process_hic_data() {
    local input_file="$1"
    local output_file="$2"
    
    log_info "Processing Hi-C contact matrix..."
    
    # Ensure output directory exists
    mkdir -p "$(dirname "$output_file")"
    
    # Validate and convert to .cool format if necessary
    # This step ensures the matrix is query-ready for FR-014 validation
    python << EOF
import cooler
import sys
import os

input_file = "$input_file"
output_file = "$output_file"

try:
    # Check if input is already a valid cooler file
    if input_file.endswith('.cool') and cooler.is_cooler(input_file):
  log_msg = f"Input file {input_file} is already a valid .cool file."
  print(log_msg)
  # Copy to output location
  import shutil
  shutil.copy2(input_file, output_file)
    else:
  # Attempt to load as generic matrix and convert
  # Note: In a real scenario, we would need to know the specific format
  # of the source data (e.g., .hic, .matrix, .mcool).
  # For this implementation, we assume the source provides a .cool or we
  # need to convert from a specific known format.
  
  # Placeholder for format-specific conversion logic
  # If the source is .hic (Juicer), we would use hic2cool
  # If the source is raw matrix, we would use cooler.cload
  
  if input_file.endswith('.hic'):
      log_msg = "Detected .hic format. Requires hic2cool conversion."
      print(log_msg)
      # Placeholder: In a real run, this would call hic2cool
      # subprocess.run(["hic2cool", "convert", input_file, output_file], check=True)
      log_msg = "Conversion logic for .hic format not fully implemented in this script."
      print(log_msg)
      sys.exit(1)
  else:
      log_msg = f"Unknown input format: {input_file}. Expected .cool or .hic."
      print(log_msg)
      sys.exit(1)
      
    # Verify output
    if cooler.is_cooler(output_file):
  print(f"Successfully created query-ready matrix: {output_file}")
    else:
  print(f"Error: Output file {output_file} is not a valid .cool file.")
  sys.exit(1)
  
except Exception as e:
    print(f"Error processing Hi-C data: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        log_error "Failed to process Hi-C data."
        exit 1
    fi

    log_info "Hi-C data processing complete: $output_file"
}

# Cleanup temporary files
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "$HIC_TEMP_DIR"
}

# Main execution
main() {
    log_info "Starting T042: Load Hi-C contact matrix"
    
    check_dependencies
    
    # Read accession from manifest (hardcoded for this task based on description, 
    # but verified against manifest.yaml)
    # The task description mentions GSE12345. We verify it exists in manifest.yaml.
    local accession="GSE12345"
    
    verify_manifest_accession "$accession"
    
    # In a real scenario, we would extract the URL from manifest.yaml
    # For this implementation, we use a placeholder URL that would fail if the data
    # doesn't exist, satisfying the "fail loudly" requirement.
    # The actual URL should be defined in manifest.yaml under 'hic' -> 'url'
    
    local url
    url=$(python -c "
import yaml
with open('$MANIFEST_FILE', 'r') as f:
    data = yaml.safe_load(f)
    hic_entries = data.get('hic', [])
    for entry in hic_entries:
  if entry.get('accession') == '$accession':
      print(entry.get('url', ''))
      break
" 2>/dev/null)
    
    if [ -z "$url" ]; then
        log_error "No URL found for accession $accession in manifest."
        log_error "The pipeline must abort if data is missing (FR-001)."
        exit 1
    fi
    
    download_hic_data "$accession" "$url"
    
    # Process the downloaded data
    process_hic_data "${HIC_TEMP_DIR}/${accession}.cool" "$HIC_OUTPUT_FILE"
    
    cleanup
    
    log_info "T042 completed successfully."
}

main "$@"