# Implementation Plan: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Branch**: `001-t-violation-beta-decay` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-t-violation-beta-decay/spec.md`

## Summary

This project performs a meta-analysis of published T-violation correlation coefficients (D-coefficients) from the NNDC ENSDF database to establish a combined upper bound on Time-Reversal symmetry violation in beta decay for specific nuclei (6He, 19Ne). The technical approach involves retrieving archival data (with a static fallback), harmonizing uncertainties, performing inverse-variance weighted meta-analysis (with Random Effects fallback), and validating results against Particle Data Group (PDG) constraints. The implementation strictly adheres to the project constitution's requirement for reproducibility, data hygiene, and statistical rigor. **Note on Methodology**: Due to the absence of raw event-level data in the source (aggregated D-coefficients only), the original Constitution Principle VII (permuting raw momentum/polarization bins) is implemented as a **Sign-Flip Permutation Test** on the aggregated D-coefficients. This is the statistically valid analog for meta-analysis and satisfies the *intent* of the constitutional requirement (generating a null distribution to test D=0) while respecting the data constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `numpy`, `scipy`, `pyyaml`, `pytest`  
**Storage**: Local CSV/JSON artifacts under `data/` (checksummed), no external database required beyond API access.  
**Testing**: `pytest` with unit tests for statistical formulas and integration tests for data retrieval (mocked for CI stability).  
**Target Platform**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).  
**Project Type**: Data Analysis / Scientific Computing CLI.  
**Performance Goals**: Complete meta-analysis pipeline within 6 hours; data retrieval must handle API rate limits via exponential backoff.  
**Constraints**: Must run on CPU; no GPU acceleration required for statistical meta-analysis.  
**Scale/Scope**: Limited to specific nuclei (6He, 19Ne) and published D-coefficients; dataset size is small (tens to hundreds of entries).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External data fetched from canonical sources (NNDC API, PDG static reference) on every run. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations to PDG and NNDC validated against the "Verified datasets" block. No fabricated URLs. PDG data loaded from verified static reference or hardcoded fallback. |
| **III. Data Hygiene** | **PASS** | Raw data retrieved via script saved to `data/raw/`. Derived data saved to `data/derived/`. Checksums recorded in `state/`. No in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics generated programmatically from `data/derived/`. No hand-typed values in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked for all artifacts. `updated_at` timestamps managed by the Advancement-Evaluator workflow. |
| **VI. Cross-Modal Statistical Independence** | **PASS** | The D-coefficient is the measure of correlation; we do not merge raw spectra. **Independence applies to the *measurements* (D-values from distinct experiments), not the underlying kinematic variables.** The meta-analysis treats each published D-coefficient as an independent random variable, which is the correct statistical interpretation for this data regime. |
| **VII. Null-Hypothesis Rigor via Permutation Testing** | **PASS with Modification** | **Modification**: The original requirement ("shuffling polarization values to momentum bins") is physically impossible as the source data (NNDC ENSDF) contains only *aggregated D-coefficients*, not raw event-level momentum/polarization pairs. **Implementation**: We implement a **Sign-Flip Permutation Test** on the aggregated D-coefficients. This is the standard randomization test for meta-analysis when raw data is unavailable. It generates a null distribution for the *weighted mean* by randomly flipping the signs of the D-coefficients (simulating D=0) and recalculating the meta-analytic average. This preserves the *intent* of the constitutional requirement (testing D=0 against a null distribution) while respecting the data constraints. |

## Project Structure

### Documentation (this feature)

```text
specs/001-t-violation-beta-decay/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── d_measurement.schema.yaml
│   └── meta_analysis_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-400-can-publicly-available-data-reveal-subtl/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_retrieval.py      # NNDC ENSDF API interaction (optional) + Static Fallback
│   ├── meta_analysis.py       # Weighted average, Cochran's Q, Random Effects fallback
│   ├── permutation_test.py    # Sign-Flip Permutation on D-coefficients
│   ├── validation.py          # PDG comparison (static reference)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded CSV/JSON from NNDC (if successful)
│   ├── derived/               # Harmonized datasets, results
│   └── checksums.txt          # Artifact hashes
├── tests/
│   ├── unit/
│   │   ├── test_meta_analysis.py
│   │   └── test_permutation.py
│   └── integration/
│       └── test_data_pipeline.py
└── paper/
    └── results.md             # Auto-generated from data
```

**Structure Decision**: Single project structure selected. The project is a linear data pipeline (Retrieve -> Harmonize -> Analyze -> Validate) without complex frontend/backend separation. All logic resides in `code/` for direct execution and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sign-Flip Permutation Module** | Required by Constitution Principle VII (modified) to establish null-hypothesis significance rigorously on aggregated data, as raw bin shuffling is impossible. | Analytic p-values alone are insufficient to prove the result isn't an artifact of the specific archival dataset structure. |
| **Random Effects Model** | Required to handle potential shared systematic uncertainties (heterogeneity) that a Fixed Effect model would underestimate. | Fixed Effect model assumes all studies share the same true effect, which is risky for T-violation data with varying experimental conditions. |
| **Static Fallback Data** | Required because no verified programmatic API exists for NNDC ENSDF or PDG D-coefficients. Ensures the pipeline runs reproducibly. | Relying solely on fragile HTML scraping would cause the pipeline to fail on CI, producing no results. |
| **Robust Retry Logic** | Required by Edge Cases in spec (NNDC API 404/timeout) to ensure high retrieval success rate (SC-005). | Simple `requests.get` without backoff would fail on transient network issues, breaking the pipeline. |