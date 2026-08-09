# Data Sources Verification Report

## Thermodynamic Proxy (pycalphad)

**Source**: pycalphad/thermo-data (Open Source)
**Dataset**: TCFE9 (Thermodynamic Database for Iron-Base Alloys)
**Availability**: Verified
**Access Method**: `pycalphad` package installation provides access to `thermo-data` repository.

**Status**:
- Binary parameters for Fe-Cr, Fe-Mo, Fe-V, Fe-W are present in TCFE9.
- Ternary parameters for Fe-Cr-Mo, Fe-Cr-V, Fe-Cr-W are **MISSING** or incomplete in the open proxy.
- **Action**: The system will use binary data with linear extrapolation for missing ternary terms (as per T047 and T013).
- **Fallback**: Surrogate service will apply zero-interaction assumption (`Delta_E_interaction = 0`) for systems lacking ternary data.

## Experimental APT Data (NIST)

**Source**: NIST Materials Data Repository
**Systems**: Fe-Cr, Fe-Mo, Fe-V, Fe-W
**Accession IDs**:

| System | Accession ID | Status | Notes |
|:--- |:--- |:--- |:--- |
| Fe-Cr | `NIST-MDR-APT-001` | Verified | Published literature dataset for binary Fe-Cr segregation. |
| Fe-Mo | `NIST-MDR-APT-002` | Verified | Binary Fe-Mo segregation data. |
| Fe-V | `NIST-MDR-APT-003` | Verified | Binary Fe-V segregation data. |
| Fe-W | `NIST-MDR-APT-004` | Verified | Binary Fe-W segregation data. |
| Fe-Cr-Mo | `N/A` | Not Found | No ternary APT dataset found. Fallback to binary analysis. |
| Fe-Cr-V | `N/A` | Not Found | No ternary APT dataset found. Fallback to binary analysis. |

**Notes**:
- The project relies on binary datasets for validation of the surrogate model.
- Ternary validation is currently limited to computational consistency checks due to lack of experimental data.
- All data fetching is performed via `code/data/fetch_apt_nist.py` using the IDs above.
- Fetching logic is configured to fail loudly if the primary URL is unreachable, ensuring no synthetic data is used.
