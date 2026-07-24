#!/bin/bash
# install_tools.sh
# Installs HISAT2, fastp, and featureCounts system packages.
# This script handles dependencies and ensures binaries are available in PATH.

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== Plant Defense Pipeline: Tool Installation Script ==="
echo "Target: Install HISAT2, fastp, featureCounts"

# Detect OS and Package Manager
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "ERROR: Unable to detect OS. Please install tools manually."
    exit 1
fi

echo "Detected OS: $OS"

install_dependencies() {
    echo ">>> Installing system dependencies..."
    case $OS in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y wget curl build-essential cmake libncurses5-dev libncursesw5-dev
            ;;
        centos|rhel|fedora)
            sudo dnf install -y wget curl gcc gcc-c++ make cmake ncurses-devel
            ;;
        macos)
            echo "macOS detected. Using Homebrew for dependencies if available."
            if ! command -v brew &> /dev/null; then
                echo "ERROR: Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            brew install cmake wget
            ;;
        *)
            echo "WARNING: Unknown OS distribution '$OS'. Attempting generic installation."
            ;;
    esac
}

install_fastp() {
    echo ">>> Installing fastp..."
    # fastp is a single binary, easiest to fetch from GitHub releases
    FASTP_VERSION="0.23.4"
    if [ "$OS" = "macos" ]; then
        FASTP_FILE="fastp_macos"
    elif [ "$(uname -m)" = "aarch64" ]; then
        FASTP_FILE="fastp_linux_aarch64"
    else
        FASTP_FILE="fastp_linux"
    fi

    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    wget -q "https://github.com/OpenGene/fastp/releases/download/v${FASTP_VERSION}/${FASTP_FILE}"
    chmod +x "${FASTP_FILE}"
    sudo mv "${FASTP_FILE}" /usr/local/bin/fastp
    cd - > /dev/null
    rm -rf "$TEMP_DIR"

    if command -v fastp &> /dev/null; then
        echo "fastp installed successfully."
        fastp --version
    else
        echo "ERROR: fastp installation failed or not in PATH."
        exit 1
    fi
}

install_hisat2() {
    echo ">>> Installing HISAT2..."
    HISAT2_VERSION="2.2.1"
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if [ "$OS" = "macos" ]; then
        wget -q "https://github.com/DaehwanKimLab/hisat2/releases/download/v${HISAT2_VERSION}/hisat2-${HISAT2_VERSION}-macos.zip"
        unzip -q "hisat2-${HISAT2_VERSION}-macos.zip"
        sudo mv hisat2-${HISAT2_VERSION}/hisat2* /usr/local/bin/
    else
        wget -q "https://github.com/DaehwanKimLab/hisat2/releases/download/v${HISAT2_VERSION}/hisat2-${HISAT2_VERSION}-linux.zip"
        unzip -q "hisat2-${HISAT2_VERSION}-linux.zip"
        sudo mv hisat2-${HISAT2_VERSION}/hisat2* /usr/local/bin/
    fi

    cd - > /dev/null
    rm -rf "$TEMP_DIR"

    if command -v hisat2 &> /dev/null; then
        echo "HISAT2 installed successfully."
        hisat2 --version | head -n 1
    else
        echo "ERROR: HISAT2 installation failed or not in PATH."
        exit 1
    fi
}

install_featurecounts() {
    echo ">>> Installing featureCounts (via Subread)..."
    # featureCounts is part of the Subread package
    SUBREAD_VERSION="2.0.3"
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if [ "$OS" = "macos" ]; then
        # macOS binary might be tricky, fallback to source or brew if binary fails
        # For robustness, we attempt brew first as it handles dependencies well on Mac
        if brew list subread &> /dev/null; then
            echo "Subread already installed via Homebrew."
        else
            brew install subread
        fi
    else
        # Linux binary
        if [ "$(uname -m)" = "aarch64" ]; then
            SUBREAD_FILE="subread-${SUBREAD_VERSION}-Linux_aarch64.tar.gz"
        else
            SUBREAD_FILE="subread-${SUBREAD_VERSION}-Linux_x86_64.tar.gz"
        fi
        
        wget -q "https://github.com/subread-team/subread/releases/download/v${SUBREAD_VERSION}/${SUBREAD_FILE}"
        tar -xzf "${SUBREAD_FILE}"
        sudo cp subread-${SUBREAD_VERSION}-Linux_x86_64/bin/featureCounts /usr/local/bin/
        sudo cp subread-${SUBREAD_VERSION}-Linux_x86_64/bin/subread-buildindex /usr/local/bin/ # Optional helper
    fi

    cd - > /dev/null
    rm -rf "$TEMP_DIR"

    if command -v featureCounts &> /dev/null; then
        echo "featureCounts installed successfully."
        featureCounts -v
    else
        echo "ERROR: featureCounts installation failed or not in PATH."
        exit 1
    fi
}

verify_installation() {
    echo ">>> Verifying all tools..."
    local failed=0

    if ! command -v fastp &> /dev/null; then
        echo "FAIL: fastp not found in PATH"
        failed=1
    fi

    if ! command -v hisat2 &> /dev/null; then
        echo "FAIL: hisat2 not found in PATH"
        failed=1
    fi

    if ! command -v featureCounts &> /dev/null; then
        echo "FAIL: featureCounts not found in PATH"
        failed=1
    fi

    if [ $failed -eq 0 ]; then
        echo "=== SUCCESS: All tools installed and verified in PATH ==="
        echo "fastp: $(which fastp)"
        echo "hisat2: $(which hisat2)"
        echo "featureCounts: $(which featureCounts)"
    else
        echo "=== FAILURE: Some tools are missing. Check logs above. ==="
        exit 1
    fi
}

main() {
    install_dependencies
    install_fastp
    install_hisat2
    install_featurecounts
    verify_installation
}

main "$@"
