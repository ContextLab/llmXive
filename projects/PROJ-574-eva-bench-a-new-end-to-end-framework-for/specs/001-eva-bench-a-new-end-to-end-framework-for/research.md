# Research: EVA-Bench Reproduction & Validation

## Executive Summary

This research validates the feasibility of reproducing the EVA-Bench framework's documentation artifacts using the vendored `dlbook_notation` codebase. The primary challenge is ensuring the LaTeX build process completes successfully on a CPU-only CI runner without missing system dependencies (TeX Live) or encountering GPU-specific errors. The strategy relies on a "build-and-validate" approach: executing the build, capturing logs, and programmatically verifying the output against the spec's success criteria (file size, content presence, error logs).

## Dataset Strategy

**Note**: This project does not use an external statistical dataset. The "data" consists of:
1.  **Source Code**: The `dlbook_notation` repository (vendored via Git submodule).
2.  **Build Artifacts**: The generated PDFs and logs.
3.  **Reference Text**: The EVA-Bench paper (for metric definitions like "EVA-A", "EVA-X").

| Data Source | Type | Verification Status | Usage in Plan |
|-------------|------|---------------------|---------------|
| `dlbook_notation` (Git Submodule) | Source Code | Verified (Assumed valid per spec assumptions) | Input for `make.sh` |
| EVA-Bench Paper (PDF) | Reference | Verified (Publicly available) | Reference for text extraction validation |
| GitHub Actions Runner (Ubuntu) | Environment | Verified (Standard CI) | Execution target |

**No external datasets** (e.g., CSV, SQL, HuggingFace) are required for this reproduction step. The "EVA-A" and "EVA-X" metrics are validated by searching for these strings in the generated PDF text, not by computing them from a dataset.

## Methodology & Statistical Rigor

Since this is a **software reproduction** task rather than a statistical study, standard statistical power analysis and causal inference assumptions are not applicable. Instead, rigor is ensured through:

1.  **Deterministic Execution**: The `make.sh` script is run in a clean environment to ensure reproducibility.
2.  **Automated Validation**: Success is defined by strict, measurable criteria (file size > 50KB, zero GPU errors) rather than subjective review.
3.  **Error Logging**: All stderr output is captured and parsed to detect "CUDA" or "GPU" keywords (SC-005).
4.  **Content Verification**: Text extraction from the PDF (using `pdftotext` or similar) confirms the presence of required metric definitions.

**Limitations**:
- Visual fidelity (e.g., font rendering, layout) is only partially validated via file size and text extraction. Full visual diffing would require baseline images (not provided in spec).
- The plan assumes the `dlbook_notation` codebase is syntactically correct. If the source is corrupted, the build will fail, and the report will reflect this as a "Fail" status.

## Feasibility Analysis (Compute Constraints)

**Target Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM, ~14GB Disk).

| Component | Requirement | Feasibility | Mitigation |
|-----------|-------------|-------------|------------|
| TeX Live Installation | ~2-4 GB disk | **Feasible** | Pre-installed in `ubuntu-latest` runner; no install needed. |
| LaTeX Compilation | CPU only | **Feasible** | `pdflatex` runs efficiently on 2 cores; no GPU needed. |
| PDF Validation | Minimal RAM | **Feasible** | `pdftotext` or `qpdf` uses < 100MB RAM. |
| Total Runtime | < 300s | **Feasible** | Simple LaTeX documents compile in < 30s. |

**Risk**: The `make.sh` script might attempt to install packages or use network resources.
**Mitigation**: The plan includes a check for network dependency errors in the log. If `make.sh` requires interactive input, it will be flagged as a failure in `reproduction_report.md`.

## Decision Rationale

- **Why CPU-only?**: The spec explicitly forbids GPU usage (FR-001, SC-005) and targets a free-tier runner. LaTeX compilation is inherently CPU-bound.
- **Why Python for validation?**: Python provides robust libraries (`PyPDF2`, `pdfminer`) for text extraction and file inspection, making it easier to automate the "text presence" checks than pure Bash.
- **Why not visual diff?**: The spec does not provide baseline images for comparison. Without a ground truth image, visual diffing is impossible. Text-based validation is the most rigorous alternative.
