# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-001 requires downloading resting-state fMRI + paired MER scores from the HCP Subjects Release with checksums. The plan's Tasks 0.1/0.2 download only the Verified Datasets URLs, which the plan itself states contain none of the required variables. No plan element satisfies FR-001; the spec's core data-acquisition requirement is unbacked. The spec (and its Verified Datasets block) is the root cause — route to clarified to either supply a genuinely verified source or revise FR-001's scope.
- FR-002 mandates fMRIPrep CPU-only preprocessing with motion correction and bandpass filtering. The coverage map entry is "Documented deviation (no raw fMRI obtainable)" — i.e., no task, contract, or phase implements it. An unimplemented MUST-level FR cannot be closed by a deviation note in the plan; the spec must be revised (or a data source supplied) so FR-002 is either backed or removed.
- FR-003 requires extracting time series from the Schaefer 200 atlas and computing Pearson FC matrices. Task 1.1 only reconstructs matrices from pre-existing fc_upper_tri vectors; no plan element performs time-series extraction or Pearson correlation. This is a distinct FR silently absorbed into the FR-002 deviation without being listed in the coverage map as such — the map claims FR-003 is "Covered by Task 1.1", which is inaccurate.
