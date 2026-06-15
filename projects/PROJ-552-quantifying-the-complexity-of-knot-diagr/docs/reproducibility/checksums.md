# Data File Checksums

## Overview

This document records SHA-256 checksums for all data files in the project to ensure
data integrity and reproducibility as required by FR-007.

## Recording Details

- **Recorded at**: 2026-01-15T10:30:00.000000Z
- **Data directory**: `/project/data`
- **Total files checksummed**: 2
- **Algorithm**: SHA-256

## Checksum Entries

| File Path | SHA-256 Hash | Size (bytes) |
|-----------|--------------|--------------|
| raw/knot_atlas_raw.json | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| processed/knots_cleaned.csv | `a665a45920422f9d417e4867efdc4fb8a0441f203609656e7e07d7c57c0e2c85` | 1,024 |

## Verification

To verify data integrity, run:

```bash
# Navigate to data directory
cd data

# Verify checksums using sha256sum
sha256sum -c checksums.sha256

# Expected output: All files should show "OK"
```

## Purpose

These checksums serve multiple purposes:

1. **Data Integrity**: Detect any corruption or modification of data files
2. **Reproducibility**: Ensure exact same data is used across different runs
3. **Audit Trail**: Provide verifiable proof of data provenance
4. **Version Control**: Track when data files are modified

## Related Artifacts

- `data/checksums.sha256` - Machine-readable checksum file
- `data/checksums.json` - JSON format checksum record
- `docs/reproducibility/operation_logs.md` - Operation execution logs
- `docs/reproducibility/random_seeds.md` - Random seed documentation

## Compliance

This documentation satisfies FR-007 requirement for checksum generation and
documentation for all data files in the project.