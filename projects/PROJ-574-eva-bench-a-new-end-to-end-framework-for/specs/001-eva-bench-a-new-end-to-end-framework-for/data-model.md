# Data Model: EVA-Bench Reproduction & Validation

## Overview

This document defines the data structures and file formats used in the EVA-Bench reproduction workflow. The "data" consists of input source files, build logs, and output artifacts. The model is static (file-based) rather than database-driven.

## Input Schema

### 1. Source Code (`external/dlbook_notation/`)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `*.tex` | File | LaTeX source documents | Must contain valid LaTeX syntax. |
| `*.cls` | File | LaTeX class files | Required for compilation. |
| `make.sh` | File | Build script | Must be executable (`chmod +x`). |
| `*.bib` | File | Bibliography (optional) | If present, must be valid BibTeX. |

### 2. Environment (`GitHub Actions Runner`)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `OS` | String | Operating System | Must be `ubuntu-latest` (Linux). |
| `texlive_version` | String | TeX Live version | Must be >= 2023 (assumed). |
| `available_disk` | Integer | Free disk space | Must be > 5GB. |

## Output Schema

### 1. Build Artifacts

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `notation_example.pdf` | File | Generated PDF | Size > 50KB, < 10MB. |
| `*.log` | File | Build log | Must contain no "fatal" errors. |
| `*.aux`, `*.out` | File | Auxiliary files | Generated during build. |

### 2. Validation Report (`reports/reproduction_report.md`)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `status` | String | "Pass" or "Fail" | Based on SC-001 to SC-005. |
| `execution_time` | Integer | Seconds taken | Must be < 300s (SC-001). |
| `gpu_errors` | Integer | Count of GPU errors | Must be 0 (SC-005). |
| `warnings` | Array[String] | List of warnings | Non-fatal issues. |
| `discrepancies` | Array[String] | List of deviations | Differences from spec. |

## Data Flow

1.  **Ingest**: `git submodule update --init` populates `external/dlbook_notation/`.
2.  **Process**: `./make.sh` is executed.
    -   Input: Source files.
    -   Output: PDF, Logs, Aux files.
3.  **Validate**: `scripts/validate_build.py` runs.
    -   Input: PDF, Logs.
    -   Logic: Check file size, extract text, scan for "CUDA"/"GPU".
    -   Output: `reproduction_report.md`.
4.  **Archive**: Artifacts and report are stored in the CI artifact store.
