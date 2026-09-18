# Design Change Log

## Critical Design Change #2: Human-Rated Ambiguity
**Date**: 2023-10-27
**Status**: Applied

**Original Spec**: Allowed synthetic derivation of ambiguity scores if human ratings were missing.
**Plan Amendment**: Ambiguity scores MUST be human-rated. If human-rated ambiguity is unavailable, the system MUST halt. NO synthetic derivation is allowed.

**Implementation**:
- `code/data/preprocess.py` includes `load_human_rated_ambiguity` and a verification gate (`T022b`).
- The system halts with a clear error message if human data is missing.

## Critical Design Change #3: Associational Framing
**Date**: 2023-10-27
**Status**: Applied

**Requirement**: All model outputs and reports must frame findings as associational, not causal.
**Implementation**:
- `code/models/lmm.py` appends "Associational analysis only; not causal" to results.
- `code/reports/generate_report.py` includes this phrase in the PDF generation logic.

## Critical Design Change #4: Linkage Integrity
**Date**: 2023-10-27
**Status**: Applied

**Requirement**: If linkage metadata is missing, the system halts. No synthetic linkage derivation.
**Implementation**:
- `code/data/ingest.py` includes a linkage verification gate (`T016`).
- The system halts if linkage is <90% of trials.
