# Artifact Hashing Utility Specification

## Overview
This module provides utilities for generating and verifying SHA-256 checksums for all intermediate and final files in the evolutionary pressure analysis pipeline. This ensures data integrity and reproducibility.

## Functional Requirements

### FR-HASH-001: Single File Hashing
The system shall calculate the SHA-256 hash of any given file.
- Input: File path
- Output: Hexadecimal string (64 characters)
- Constraint: Must handle large files (e.g., BAMs > 1GB) by reading in chunks (64KB buffer).

### FR-HASH-002: Manifest Generation
The system shall generate a JSON manifest containing hashes for a list of files.
- Input: List of file paths, optional output path
- Output: JSON object mapping relative paths to hashes
- Behavior: If output path is provided, write JSON to disk.

### FR-HASH-003: Manifest Verification
The system shall verify the integrity of files against a stored manifest.
- Input: Path to manifest JSON
- Output: Boolean (True if all valid, False if any mismatch)
- Logging: Must log detailed error messages for mismatches or missing files.

### FR-HASH-004: Error Handling
- Missing files must raise `FileNotFoundError` during hashing.
- Directories must raise `IsADirectoryError` during hashing.
- Permission errors must be logged and re-raised as `PermissionError`.

## Integration Points
- Used by `src/pipeline/hash_manifest.py` to generate `artifacts_manifest.json`.
- Used by `src/pipeline/lifecycle.py` to verify file integrity before deletion.
- Used by `src/pipeline/download.py` to verify downloaded FASTQ integrity.

## Performance Considerations
- Hashing must be efficient enough to process multi-gigabyte BAM files without excessive memory usage.
- Manifest generation should be parallelized if processing hundreds of files (future enhancement).

## Security Considerations
- SHA-256 is collision-resistant and suitable for integrity verification.
- Hashes are stored in plain text JSON; no encryption required for this use case.
