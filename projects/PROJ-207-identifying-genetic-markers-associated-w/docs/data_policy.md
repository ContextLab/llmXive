# Data Policy: Immutability of Raw Data

## Purpose

This document defines the immutable constraint for raw data within the
`PROJ-207-identifying-genetic-markers-associated-w` project. It establishes
the rules for handling data ingested from external sources (e.g., NCBI BioProject,
Ensembl) to ensure reproducibility, auditability, and scientific integrity.

## Scope

This policy applies to all data files located in the `data/raw/` directory.
These files represent the unaltered, original source data as downloaded or
received.

## Immutable Constraint Definition

**Raw data is immutable.** Once a file is placed in `data/raw/`, it must
never be modified, deleted, overwritten, or appended to.

### Operational Rules

1. **Write-Once**: Data in `data/raw/` is written exactly once during the
 ingestion process (e.g., by `code/01_download.py` or manual transfer).
2. **Read-Only Access**: All analysis scripts must treat files in `data/raw/`
 as read-only. No script is permitted to open these files in write mode.
3. **Checksum Verification**: Integrity is maintained via SHA-256 checksums.
 The `code/utils/checksum_verify.py` utility must be run to verify that
 raw data files match their recorded hashes before any processing begins.
 Any mismatch indicates data corruption or tampering and must halt the pipeline.
4. **No In-Place Transformation**: Any transformation, cleaning, filtering,
 or format conversion must result in a *new* file written to a different
 directory (e.g., `data/interim/`, `data/processed/`). The original file
 in `data/raw/` remains untouched.

## Rationale

- **Reproducibility**: Scientific results must be reproducible. If the input
 data changes, the results may change. Immutability ensures that the exact
 input used for a specific analysis can be retrieved and re-used.
- **Auditability**: In the event of an error or anomaly, investigators must
 be able to trace results back to the exact original source data without
 ambiguity.
- **Data Integrity**: Prevents accidental corruption or accidental overwriting
 of critical source material during experimental runs.

## Directory Structure Enforcement

The project directory structure enforces this policy:

- `data/raw/`: **Immutable**. Contains original source files (e.g., `.vcf`, `.fastq`).
- `data/interim/`: **Mutable**. Contains intermediate files generated during
 processing (e.g., aligned BAMs, cleaned phenotypes). These files may be
 overwritten by subsequent pipeline runs.
- `data/processed/`: **Mutable**. Contains final analysis outputs (e.g.,
 GWAS results, FDR-corrected tables). These files may be overwritten.

## Violation Handling

Any attempt to modify a file in `data/raw/` is considered a critical policy
violation. The pipeline must halt with an error if it detects that a raw
file has been modified since its last checksum verification.

## Versioning

If a new version of the source data becomes available (e.g., a corrected
genome assembly), the new data must be downloaded to a *new* location within
`data/raw/` (e.g., `data/raw/v2/` or with a versioned filename). The old
version must remain intact for historical reproducibility.

## Related Artifacts

- `code/utils/checksum_verify.py`: Utility to verify raw data integrity.
- `data/raw/.checksums`: Manifest file containing SHA-256 hashes for all raw files.
- `data/raw/`: Directory containing immutable source data.