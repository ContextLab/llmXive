# Data Sources and Verification Log

## Thermodynamic Proxy (TCFE.tdb)

**Source**: Open Calphad Database (TCFE9)
**URL**:
**DOI**: (Placeholder - replace with actual DOI once verified)
**Verification Date**: 2026-06-13
**Verification Status**: PENDING

### Ternary Parameter Verification

The following ternary systems are required for this project:
- Fe-Cr-Mo
- Fe-Cr-V
- Fe-Mo-V
- Fe-Cr-W
- Fe-Mo-W

**Validation Result**:
- The database file `TCFE.tdb` was downloaded from the open Calphad repository.
- A text-based validation was performed to check for the presence of ternary interaction parameters.
- **Note**: The validation logic is currently a simplified heuristic. A robust validation using pycalphad is recommended for production use.
- **Status**: The validation script (`code/data/fetch_thermo_proxy.py`) is designed to fail loudly if any of the required ternary parameters are missing.

### NIST APT Dataset Accession IDs

The following NIST APT datasets are identified for the binary systems:
- Fe-Cr: NIST-APT-XXXXX (To be verified in T045a)
- Fe-Mo: NIST-APT-XXXXX (To be verified in T045a)
- Fe-V: NIST-APT-XXXXX (To be verified in T045a)
- Fe-W: NIST-APT-XXXXX (To be verified in T045a)

**Verification Status**: Pending (See T045a)

## References

1. Calphad Open Databases. https://calphad.org/
2. pycalphad. https://pycalphad.org/
3. NIST Atom Probe Tomography Database. https://www.nist.gov/