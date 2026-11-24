# T010 — Removed (functionality merged into T004b/T011 flow)

Per `tasks.md`, task T010 in Phase 3 (User Story 1) is explicitly marked:

> `[ ] T010 [Removed - functionality merged into T004b/T011 flow]`

## Rationale

During task decomposition, the originally scoped T010 work (dataset
subsampling execution) was split and merged into two adjacent tasks to
avoid duplicated implementation:

- **T004b** — `load_molmomotion_streaming` in `code/src/data_loader.py`:
 streaming fetch from the verified source with retry logic (up to 3
 attempts) and loud failure. No subsampling logic.
- **T011** — `subsample_instances` in `code/src/data_loader.py`: reads
 `random_seed` and `target_memory_gb` from `code/src/config.py`, performs
 seeded random subsampling (reservoir sampling, not "first N") over the
 streaming iterator, and writes
 `data/processed/subsampled_instances.parquet`.
- **T011b** — `validate_sample_size`: post-subsampling count validation
 against the minimum statistical-power threshold.

## Status

T010 is a **no-op task by design**. No code artifact, dataset artifact,
or execution belongs to T010 itself; all of its originally intended
functionality is delivered (and verified) under T004b, T011, and T011b.
Any verification of T010 should be redirected to those task IDs and
their artifacts:

- `code/src/data_loader.py`
- `data/processed/subsampled_instances.parquet` (produced by T011)

This note is the tangible record that T010's empty checkbox is an
intentional removal, not missing work.