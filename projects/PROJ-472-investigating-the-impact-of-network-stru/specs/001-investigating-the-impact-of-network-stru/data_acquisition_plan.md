# Data‑Acquisition Plan for Matched dMRI + EEG Participants

**Project:** Investigating the Impact of Network Structure on Neural Avalanche Dynamics
**Feature Branch:** `001-network-structure-avalanche-dynamics`
**Date:** 2026‑10‑12

## 1. Objective

Obtain a set of human participants for which **both** diffusion‑MRI (dMRI) tractography data and resting‑state EEG recordings are publicly available, and ensure that the two modalities are correctly indexed to the same subject identifiers. This matched dataset will serve as the foundation for all downstream preprocessing, metric computation, and statistical association steps.

## 2. Data Sources

| Modality | OpenNeuro Dataset ID | URL | Expected File Structure |
|----------|----------------------|-----|--------------------------|
| dMRI (tractography) | `ds004230` | <https://openneuro.org/datasets/ds004230> | `data/raw/dMRI/sub‑{subject_id}/.../*.tck` |
| Resting‑state EEG | `ds004231` | <https://openneuro.org/datasets/ds004231> | `data/raw/EEG/sub‑{subject_id}/.../*.fif` |

Both datasets follow the BIDS convention [UNRESOLVED-CLAIM: c_d4aee85e — status=not_enough_info]; the subject identifier is the `sub‑XX` folder name (e.g., `sub-01`). No additional renaming is required.

## 3. Participant Indexing Strategy

1. **Discovery**
 - List all subject directories under `data/raw/dMRI/` → `dMRI_subjects`.
 - List all subject directories under `data/raw/EEG/` → `EEG_subjects`.

2. **Matching**
 - Compute the intersection `matched_subjects = dMRI_subjects ∩ EEG_subjects`.
 - The resulting list contains the identifiers for which *both* modalities are present.

3. **Canonical Identifier**
 - Use the raw BIDS identifier (`sub‑XX`) unchanged throughout the pipeline.
 - All downstream files (connectomes, pre‑processed EEG, QC reports) will be stored under `data/processed/.../sub‑{subject_id}` to preserve traceability.

4. **Persisting the Index**
 - Write `data/processed/matched_subjects.json` with the structure:
 ```json
 {
 "subject_ids": ["01", "02", "..."]
 }
 ```
 - This file is read by downstream scripts (e.g., `preprocess_dMRI.py`, `preprocess_EEG.py`, `store.py`) to know which participants to process.

## 4. Verification Criteria for ID Alignment

After the download step (`code/data/download.py`) completes, the pipeline must verify that the subject indices are perfectly aligned. The verification consists of the following checks:

1. **Presence Check**
 - Confirm that `matched_subjects.json` exists and contains at least one subject ID.
 - If empty, abort with a clear error message indicating that no matched participants were found.

2. **Symmetry Check**
 - For each `subject_id` in `matched_subjects.json`, assert that:
 - `data/raw/dMRI/sub‑{subject_id}` contains at least one `.tck` file.
 - `data/raw/EEG/sub‑{subject_id}` contains at least one `.fif` file.
 - Missing files trigger a `FileNotFoundError` with the offending subject ID.

3. **Hash Verification (Optional but Recommended)**
 - Compute SHA‑256 checksums for each raw file and compare them against entries in `data/raw/.checksums.json`.
 - Any checksum mismatch should raise a `ValueError` and halt the pipeline, ensuring data integrity.

4. **Routing State Update**
 - Upon successful verification, `code/data/download.py` writes `data/processed/routing_state.json` with fields:
 ```json
 {
 "has_matched_eeg": true,
 "n_subjects_dMRI": <int>,
 "n_subjects_EEG": <int>,
 "matched_subjects": <int>,
 "dMRI_path": "data/raw/dMRI",
 "EEG_path": "data/raw/EEG",
 "simulation_required": false
 }
 ```
 - Downstream scripts (e.g., the sample‑size gate in `code/main.py`) rely on this file to decide whether to proceed.

## 5. Failure Modes & Reporting

- **No Overlap:** If `matched_subjects` is empty, the pipeline aborts and writes an `insufficient_sample_report.md` (handled later in T029c).
- **Partial Overlap:** If any subject is missing one modality, that subject is omitted from `matched_subjects.json`; a warning is logged with the list of excluded IDs.
- **Checksum Mismatch:** The download script raises a `ConnectionError` (per the project policy of no silent fall‑backs). The error propagates to the top‑level `main.py`, which reports the failure and exits with a non‑zero status.

## 6. Timeline & Resource Considerations

- **Streaming Download:** Files > 100 MB are streamed using `datasets.load_dataset(..., streaming=True)` to keep memory usage < 2 GB.
- **Parallelism:** The download of dMRI and EEG datasets can run in parallel (`[P]` flag) because they write to distinct sub‑folders.
- **Disk Requirements:** Approx. 10 GB total for raw data (≈ 5 GB each modality) and ~2 GB for processed outputs. The CI runner provides sufficient space.

## 7. Traceability

All steps are logged via the project‑wide logger (`code/utils/logger.py`). Each log entry includes a timestamp, the script name, and a concise message, enabling reproducible audit trails.

---

*This plan fulfills T000 by outlining the acquisition workflow, defining the participant indexing scheme, and specifying concrete verification criteria for ID alignment.*