# Data-Acquisition Plan: Matched dMRI + EEG Participant Indexing

**Project**: Investigating the Impact of Network Structure on Neural Avalanche Dynamics
**Task**: T000 — High-level data-acquisition plan
**Status**: Draft

## 1. Objective

Acquire diffusion-MRI (dMRI) tractography and resting-state EEG recordings for the
*same* participants from public OpenNeuro datasets, and build a unified,
participant-indexed data store keyed by a canonical subject identifier so that
structural connectome metrics and neural-avalanche statistics can be computed on
matched subjects only.

## 2. Data Sources

| Modality | Dataset | Accession | URL |
|----------|---------|-----------|-----|
| dMRI tractography | HCP-Aging (dMRI) | ds004230 | https://openneuro.org/datasets/ds004230 |
| Resting-state EEG | HCP-Aging (EEG) | ds004231 | https://openneuro.org/datasets/ds004231 |
| Cortical parcellation | HCP-MMP1.0 (Glasser 2016, 360 parcels) | — | |

Cross-dataset registration (pairing subjects that are not the same individuals in
both modalities) is **not permitted**: it invalidates the structure–function
research question. Only subjects present in BOTH accessions are used.

## 3. Participant Indexing Scheme

1. **Canonical ID**: BIDS-style `sub-<label>` (e.g., `sub-01`). The label is the
 zero-padded participant label as published in each dataset's
 `participants.tsv`.
2. **Per-modality index**: after download, each modality directory
 (`data/raw/dMRI/`, `data/raw/EEG/`) is scanned for `sub-*` directories; the
 set of subject labels found is recorded.
3. **Matched index**: the intersection of the two label sets is computed
 (`match_subjects` in `code/data/download.py`) and written to
 `data/processed/routing_state.json` with the fields:
 - `has_matched_eeg` (bool)
 - `n_subjects_dMRI` (int)
 - `n_subjects_EEG` (int)
 - matched subject list and data-path pointers.
4. **Unified store** (T013): `data/processed/unified_participant_store.json`
 with one record per matched subject:
 `{subject_id, structural_path, eeg_path, data_type}`.

## 4. Verification Criteria for ID Alignment

The following checks MUST pass before preprocessing is allowed to proceed; each
fails loudly (raises) rather than falling back to synthetic data:

- **V1 — Subject-set identity**: the set of subject labels under
 `data/raw/dMRI/sub-*` equals the set under `data/raw/EEG/sub-*` for the
 downloaded subset; any mismatch is logged and the unmatched subjects are
 dropped from the matched index (never silently paired).
- **V2 — Non-empty intersection**: the matched set must contain at least one
 subject; if empty, `routing_state.json` records `has_matched_eeg: false` and
 the pipeline stops with an explicit error (no simulation fallback).
- **V3 — Per-subject file presence**: for every subject in the unified store,
 both `structural_path` and `eeg_path` must exist on disk and be non-empty;
 a query for a participant ID must return both modalities without error.
- **V4 — Checksum integrity**: every downloaded raw file's SHA-256 is recorded
 in `data/raw/.checksums.json` at download time and re-verified after
 download; a mismatch raises an error.
- **V5 — Parcellation integrity**: the SHA-256 of the HCP-MMP parcellation zip
 is computed at runtime, recorded in `data/processed/parcellation_hash.json`,
 and compared against the recorded value on every subsequent run.
- **V6 — Automated test**: `tests/test_download_alignment.py` asserts that the
 subject IDs are identical across modalities after a download run.

## 5. Acquisition Workflow (high level)

1. Fetch dataset file listings from OpenNeuro for ds004230 and ds004231.
2. Extract subject lists from both listings; compute the matched set.
3. Stream-download dMRI tractography (`.tck`) and EEG (`.fif`) files for the
 matched subset into `data/raw/dMRI/` and `data/raw/EEG/` (streaming for
 large files; chunk sizes logged).
4. Verify checksums (V4) and write `routing_state.json`.
5. Download and hash-verify the HCP-MMP parcellation (V5).
6. Preprocess: dMRI → connectivity matrices via MRtrix3 `tck2connectome`
 (360 parcels); EEG → 1–40 Hz band-pass, 250 Hz down-sample, ICA cleaning
 (MNE-Python).
7. Build the unified participant store (Section 3.4) and run QC
 (`data/processed/usable_subjects.json`, `pipeline_quality_rate`).

## 6. Quality & Exclusion Criteria (downstream of acquisition)

- Subjects with >30% EEG channels removed after ICA are excluded.
- Subjects whose structural graph is disconnected (`networkx.is_connected`)
 are excluded.
- Sample-size gate: if the number of usable matched subjects is below
 `config.N_MIN` (10), the statistical stage is marked `"limited"` and an
 insufficient-sample report is produced.

## 7. Compute & Reproducibility Constraints

- All downloads stream; no file >100 MB is loaded fully into memory.
- CPU-only execution; total pipeline runtime target ≤ 6 h.
- Random seeds pinned (`config.RANDOM_SEED = 42`).
- Raw files are stored unchanged under `data/raw/`; all transformations write
 new files under `data/processed/` with provenance recorded.
- Real data only: if the real OpenNeuro fetch fails, the pipeline raises —
 no synthetic stand-in is ever generated for the primary analysis.