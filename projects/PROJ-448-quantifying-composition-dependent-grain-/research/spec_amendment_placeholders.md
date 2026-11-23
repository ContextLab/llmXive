# Spec Amendment: Placeholder Data Handling (T018a)

## Context
The original specification (FR-001, FR-002, FR-007) requires the use of real experimental and computational data sources. However, due to the constraints of the CI environment and the current availability of open-access datasets for specific ternary systems, the pipeline must be able to proceed with placeholder data where real data is verified to be absent.

## Amendment Details
This amendment explicitly permits the generation and use of "no_data" placeholder files for the following data types when a verified source cannot be found or accessed:
1. **CALPHAD Parameters**: If no open-source TCFE9 (or compatible) parameters are found, `data/raw/calphad_params_no_data.json` may be created.
2. **DFT Energies**: If no pre-computed DFT segregation energies are found for a specific system, `data/raw/dft_energies_no_data.json` (or system-specific variant) may be created.
3. **APT Data**: If no APT datasets are found for a specific binary/ternary system, `data/raw/apt_data/<system>_no_data.json` may be created.

## Constraints
- **Verification First**: A placeholder can only be created after a verification step (e.g., T045a-Verify, T045e-Verify) explicitly records "No verified source found" in `research/data_sources.md`.
- **No Silent Fallbacks**: Scripts must NOT silently fall back to synthetic data generation (e.g., `np.random`) if real data fetch fails. The failure must be explicit, and the placeholder creation logic must be triggered by the "No Data" state recorded in the verification step.
- **Downstream Handling**: Downstream tasks (e.g., T018, T021) must check for the presence of these placeholder files. If a placeholder is detected, the task should skip the specific calculation for that system and log a warning (e.g., "Skipped: No data for system X"), rather than raising a hard error.
- **Manifest Updates**: The `data_manifest.json` must be updated to reflect the status of these sources, marking them as `source_type: 'placeholder'` with a `reason` field indicating "no_source_found" or "fetch_failed".

## Scope
This amendment applies to the current CI execution of the pipeline. It does not imply that the scientific results derived from placeholders are valid for publication. It merely ensures the pipeline does not deadlock due to missing data.

## Reference
- Task T018a (Spec-amendment)
- Task T045a-Verify, T045c-Verify, T045e-Verify, T045f-Verify
- Task T045a-Fetch, T045c-Fetch, T045e-Fetch, T045f-Fetch
