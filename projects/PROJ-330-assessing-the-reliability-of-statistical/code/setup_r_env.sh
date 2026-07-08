#!/bin/bash
# Setup R 4.3+ environment with renv for reproducible genomic analysis
# Requires R 4.3+ to be installed on the system

set -e

echo "=== Setting up R environment for PROJ-330 ==="

# Check R version
R_VERSION=$(R --version | head -n 1 | awk '{print $3}')
echo "Detected R version: $R_VERSION"

# Verify R >= 4.3
if [[ $(echo "$R_VERSION < 4.3" | bc -l) -eq 1 ]]; then
    echo "ERROR: R version 4.3 or higher is required. Current version: $R_VERSION"
    exit 1
fi

# Create R project directory if it doesn't exist
mkdir -p code/scripts

# Initialize renv if not already initialized
if [ ! -f "code/scripts/renv.lock" ]; then
    echo "Initializing renv in code/scripts/..."
    R --vanilla << 'EOF'
    if (!requireNamespace("renv", quietly = TRUE)) {
        install.packages("renv", repos = "https://cloud.r-project.org")
    }
    renv::init(path = "code/scripts", bare = TRUE)
    renv::install(c("DESeq2", "edgeR", "BiocGenerics", "lattice", "ggplot2"))
    renv::snapshot(path = "code/scripts")
    cat("R environment initialized successfully.\n")
    cat("Required packages: DESeq2, edgeR, BiocGenerics, lattice, ggplot2\n")
    cat("Lockfile created at: code/scripts/renv.lock\n")
    EOF
else
    echo "R environment already initialized (renv.lock exists)."
fi

# Verify critical packages
echo "Verifying R package installation..."
R --vanilla --quiet << 'EOF'
required_packages <- c("DESeq2", "edgeR")
missing <- setdiff(required_packages, rownames(installed.packages()))
if (length(missing) > 0) {
    cat("ERROR: Missing required R packages:", paste(missing, collapse = ", "), "\n")
    cat("Please install them manually: BiocManager::install(c(\"", paste(missing, collapse = "\", \""), "\"))\n")
    quit(status = 1)
}
cat("All required R packages are installed.\n")
EOF

echo "=== R environment setup complete ==="
echo "To activate R environment in a new shell:"
echo "  source code/scripts/renv/activate.R"
echo ""
echo "To run R scripts:"
echo "  Rscript code/scripts/run_r_script.R"