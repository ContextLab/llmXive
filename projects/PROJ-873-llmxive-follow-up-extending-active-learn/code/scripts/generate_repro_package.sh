#!/bin/bash
# T051: Generate reproducibility package script
# This script creates a self-contained tarball for reproducing the llmXive results.
# It includes the code, configuration, generated data artifacts, and a run-book.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_NAME="llmXive_repro_PROJ-873_$(date +%Y%m%d%H%M%S).tar.gz"
TEMP_DIR=$(mktemp -d)

echo "📦 Creating reproducibility package: ${PACKAGE_NAME}"
echo "📂 Working directory: ${PROJECT_ROOT}"
echo "📁 Temp staging: ${TEMP_DIR}"

# 1. Create directory structure in temp
mkdir -p "${TEMP_DIR}/llmXive_repro"
mkdir -p "${TEMP_DIR}/llmXive_repro/code"
mkdir -p "${TEMP_DIR}/llmXive_repro/data"
mkdir -p "${TEMP_DIR}/llmXive_repro/tests"
mkdir -p "${TEMP_DIR}/llmXive_repro/docs"

# 2. Copy essential code files (excluding heavy dependencies/models)
# We copy the scripts and modules defined in the API surface
cp -r "${PROJECT_ROOT}/code"/*.py "${TEMP_DIR}/llmXive_repro/code/" 2>/dev/null || true
cp -r "${PROJECT_ROOT}/code/scripts"/*.py "${TEMP_DIR}/llmXive_repro/code/scripts/" 2>/dev/null || true
cp -r "${PROJECT_ROOT}/code/audit"/*.py "${TEMP_DIR}/llmXive_repro/code/audit/" 2>/dev/null || true

# Copy configuration and requirements
cp "${PROJECT_ROOT}/requirements.txt" "${TEMP_DIR}/llmXive_repro/" 2>/dev/null || echo "⚠ requirements.txt not found"
cp "${PROJECT_ROOT}/README.md" "${TEMP_DIR}/llmXive_repro/" 2>/dev/null || echo "⚠ README.md not found"

# Copy generated data artifacts (the results of the run)
# These are the declared deliverables from the execution log
if [ -d "${PROJECT_ROOT}/data/processed" ]; then
    cp -r "${PROJECT_ROOT}/data/processed"/* "${TEMP_DIR}/llmXive_repro/data/processed/" 2>/dev/null || true
fi
if [ -d "${PROJECT_ROOT}/data/results" ]; then
    cp -r "${PROJECT_ROOT}/data/results"/* "${TEMP_DIR}/llmXive_repro/data/results/" 2>/dev/null || true
fi
if [ -d "${PROJECT_ROOT}/data/raw" ]; then
    cp -r "${PROJECT_ROOT}/data/raw" "${TEMP_DIR}/llmXive_repro/data/" 2>/dev/null || true
fi

# 3. Generate a dynamic README for the package explaining how to reproduce
cat > "${TEMP_DIR}/llmXive_repro/REPRO_INSTRUCTIONS.md" << 'EOF'
# Reproduction Instructions for llmXive (PROJ-873)

This package contains the code and data artifacts for the "Active Learners as Efficient PRP Rerankers" study.

## Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`
- (Optional) BEIR datasets will be re-downloaded if not present in `data/raw/`.

## Steps to Reproduce

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Artifacts**:
   The `data/` directory contains the processed results from the original run.
   - `data/processed/injected_datasets.json`: Synthetic redundancy injection.
   - `data/processed/clusters.json`: MinHash-LSH clustering results.
   - `data/processed/comparison_log.jsonl`: Pairwise comparison logs.
   - `data/results/*.json`: Final metrics (NDCG, Wilcoxon tests, etc.).

3. **Re-run Validation** (Optional):
   To verify the pipeline against the existing data:
   ```bash
   python code/quickstart_validator.py
   ```

4. **Generate Charts** (Optional):
   If you have matplotlib installed:
   ```bash
   python code/scripts/generate_charts.py
   ```

## Notes
- This package does **not** include large model weights (e.g., TinyLlama, all-MiniLM-L6-v2).
- If you need to re-run the full pipeline from scratch, ensure you have sufficient CPU/RAM resources (see `specs/001-llmxive-prp-redundancy/spec.md`).
- The `data/raw/` folder may contain downloaded BEIR datasets (scifact, nfcorpus, trec-covid). If missing, the pipeline will attempt to re-download them.
EOF

# 4. Create the tarball
cd "${TEMP_DIR}"
tar -czf "${PROJECT_ROOT}/${PACKAGE_NAME}" llmXive_repro

# 5. Cleanup
rm -rf "${TEMP_DIR}"

echo "✅ Package created successfully: ${PROJECT_ROOT}/${PACKAGE_NAME}"
echo "📊 Size: $(du -h "${PROJECT_ROOT}/${PACKAGE_NAME}" | cut -f1)"
echo "📝 To verify, run: tar -tzf ${PACKAGE_NAME} | head -20"