#!/bin/bash
# T003b: System Package Installation Script for HISAT2, fastp, and featureCounts
#
# This script attempts to install the required external tools for RNA-seq preprocessing.
# It prioritizes package managers (apt, yum, brew) and falls back to source compilation
# if binaries are not available via the system package manager.
#
# Prerequisites:
# - Root/sudo access (for system packages)
# - Build tools (gcc, make, cmake, wget, unzip) for source compilation
#
# Usage:
#   bash scripts/install_system_packages.sh
#
# After execution, verify installation:
#   hisat2 --version
#   fastp --version
#   featureCounts --version

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
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

check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Determine OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
elif [ "$(uname)" == "Darwin" ]; then
    OS="macos"
else
    OS="unknown"
fi

log_info "Detected OS: $OS"

# --- Installation Functions ---

install_hisat2() {
    log_info "Checking HISAT2 installation..."
    if check_command hisat2; then
        log_info "HISAT2 is already installed: $(hisat2 --version)"
        return 0
    fi

    if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
        log_info "Attempting to install HISAT2 via apt..."
        if sudo apt-get update && sudo apt-get install -y hisat2; then
            log_info "HISAT2 installed via apt."
            return 0
        fi
    elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
        log_info "Attempting to install HISAT2 via yum..."
        if sudo yum install -y hisat2; then
            log_info "HISAT2 installed via yum."
            return 0
        fi
    elif [ "$OS" == "macos" ]; then
        log_info "Attempting to install HISAT2 via Homebrew..."
        if check_command brew; then
            if brew install hisat2; then
                log_info "HISAT2 installed via Homebrew."
                return 0
            fi
        else
            log_warn "Homebrew not found. Cannot install via brew."
        fi
    fi

    # Fallback: Compile from source
    log_warn "System package installation failed. Compiling HISAT2 from source..."
    HISAT2_VERSION="2.2.1"
    HISAT2_DIR="hisat2-${HISAT2_VERSION}"
    HISAT2_URL="https://github.com/DaehwanKimLab/hisat2/releases/download/v${HISAT2_VERSION}/hisat2-${HISAT2_VERSION}-linux_x86_64.zip"

    if ! check_command wget; then
        log_error "wget is required to download HISAT2 source/binary."
        return 1
    fi
    if ! check_command unzip; then
        log_error "unzip is required to extract HISAT2."
        return 1
    fi

    log_info "Downloading HISAT2 ${HISAT2_VERSION}..."
    wget -q "${HISAT2_URL}" -O "hisat2.zip"

    log_info "Extracting HISAT2..."
    unzip -q hisat2.zip
    rm hisat2.zip

    log_info "Installing HISAT2 to /usr/local/bin..."
    sudo cp "${HISAT2_DIR}/hisat2" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-ins" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-build" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-align-s" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-align-l" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-extract-exon" /usr/local/bin/
    sudo cp "${HISAT2_DIR}/hisat2-extract-sequence" /usr/local/bin/

    rm -rf "${HISAT2_DIR}"

    if check_command hisat2; then
        log_info "HISAT2 installed successfully from source."
        return 0
    else
        log_error "Failed to install HISAT2."
        return 1
    fi
}

install_fastp() {
    log_info "Checking fastp installation..."
    if check_command fastp; then
        log_info "fastp is already installed: $(fastp --version)"
        return 0
    fi

    if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
        log_info "Attempting to install fastp via apt..."
        # fastp might not be in default repos, try bioconda or snap if available, otherwise source
        if sudo apt-get install -y fastp 2>/dev/null; then
            log_info "fastp installed via apt."
            return 0
        fi
    elif [ "$OS" == "macos" ]; then
        log_info "Attempting to install fastp via Homebrew..."
        if check_command brew; then
            if brew install fastp; then
                log_info "fastp installed via Homebrew."
                return 0
            fi
        fi
    fi

    # Fallback: Compile from source (using pre-built binary for speed if available, else source)
    log_warn "System package installation failed. Downloading fastp binary..."
    FASTP_VERSION="0.23.4"
    FASTP_FILE="fastp_linux.zip"
    FASTP_URL="https://github.com/OpenGene/fastp/releases/download/v${FASTP_VERSION}/${FASTP_FILE}"

    if ! check_command wget; then
        log_error "wget is required."
        return 1
    fi
    if ! check_command unzip; then
        log_error "unzip is required."
        return 1
    fi

    log_info "Downloading fastp ${FASTP_VERSION}..."
    wget -q "${FASTP_URL}" -O "${FASTP_FILE}"

    log_info "Extracting fastp..."
    unzip -q "${FASTP_FILE}"
    rm "${FASTP_FILE}"

    log_info "Installing fastp to /usr/local/bin..."
    sudo cp fastp /usr/local/bin/
    sudo chmod +x /usr/local/bin/fastp

    rm -f fastp

    if check_command fastp; then
        log_info "fastp installed successfully."
        return 0
    else
        log_error "Failed to install fastp."
        return 1
    fi
}

install_featurecounts() {
    log_info "Checking featureCounts installation..."
    if check_command featureCounts; then
        log_info "featureCounts is already installed: $(featureCounts --version)"
        return 0
    fi

    # featureCounts is part of Subread package
    if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
        log_info "Attempting to install Subread (featureCounts) via apt..."
        if sudo apt-get install -y subread; then
            log_info "Subread (featureCounts) installed via apt."
            # Verify featureCounts exists (sometimes it's named differently or in a subfolder)
            if check_command featureCounts; then
                return 0
            fi
        fi
    elif [ "$OS" == "macos" ]; then
        log_info "Attempting to install Subread via Homebrew..."
        if check_command brew; then
            if brew install subread; then
                log_info "Subread installed via Homebrew."
                if check_command featureCounts; then
                    return 0
                fi
            fi
        fi
    fi

    # Fallback: Download pre-compiled binary
    log_warn "System package installation failed. Downloading Subread binary..."
    SUBREAD_VERSION="2.0.6"
    SUBREAD_FILE="subread-${SUBREAD_VERSION}-linux-x86_64.tar.gz"
    SUBREAD_URL="https://github.com/subread-team/subread/releases/download/v${SUBREAD_VERSION}/subread-${SUBREAD_VERSION}-linux-x86_64.tar.gz"

    if ! check_command wget; then
        log_error "wget is required."
        return 1
    fi
    if ! check_command tar; then
        log_error "tar is required."
        return 1
    fi

    log_info "Downloading Subread ${SUBREAD_VERSION}..."
    wget -q "${SUBREAD_URL}" -O "${SUBREAD_FILE}"

    log_info "Extracting Subread..."
    tar -xzf "${SUBREAD_FILE}"
    rm "${SUBREAD_FILE}"

    log_info "Installing featureCounts to /usr/local/bin..."
    sudo cp "subread-${SUBREAD_VERSION}-linux-x86_64/bin/featureCounts" /usr/local/bin/
    sudo chmod +x /usr/local/bin/featureCounts

    rm -rf "subread-${SUBREAD_VERSION}-linux-x86_64"

    if check_command featureCounts; then
        log_info "featureCounts installed successfully."
        return 0
    else
        log_error "Failed to install featureCounts."
        return 1
    fi
}

# --- Main Execution ---

log_info "Starting system package installation..."

FAILED=0

install_hisat2 || FAILED=1
install_fastp || FAILED=1
install_featurecounts || FAILED=1

echo ""
if [ $FAILED -eq 0 ]; then
    log_info "All packages installed successfully."
    log_info "Verification:"
    hisat2 --version 2>&1 | head -n 1
    fastp --version 2>&1 | head -n 1
    featureCounts --version 2>&1 | head -n 1
    exit 0
else
    log_error "One or more packages failed to install. Please check the logs above."
    exit 1
fi
