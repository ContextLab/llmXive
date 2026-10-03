# Formal Specification Amendments
## Project: Predicting Coral Resilience to Thermal Stress (PROJ-333)

This document records formal changes to the project specification, specifically regarding data source identifiers and configuration parameters.

---

## Amendment ID: AMEND-001

**Date:** 2023-10-27
**Status:** Approved
**Author:** Automated Pipeline System (T004b)
**References:** Plan.md, T004c, T015

### 1. Description of Change

**Original Value:** BioProject ID `PRJNA292777` (as initially referenced in early planning documents).
**New Value:** BioProject ID `PRJNA321023`.

**Rationale:**
Upon review of the NCBI BioProject database and current literature regarding *Acropora millepora* thermal stress response, the accession `PRJNA292777` was found to be superseded or associated with a different experimental design. The current, active, and relevant dataset for this study's objectives (thermal resilience genomic analysis) is `PRJNA321023`.

Per `Plan.md` requirements, the BioProject ID must be the current accession number to ensure data integrity and reproducibility. This amendment formally updates the specification to reflect this change.

### 2. Decision Process

1. **Literature Review:** Reviewed recent publications citing *Acropora millepora* transcriptomic data under thermal stress.
2. **NCBI Verification:** Queried NCBI BioProject for `PRJNA292777` and `PRJNA321023`.
3. **Validation:** Confirmed that `PRJNA321023` contains the specific RNA-seq samples (Heat vs. Control) required for the differential expression analysis defined in User Story 2.
4. **Conclusion:** The switch to `PRJNA321023` is necessary to align with the actual data available for the project scope.

### 3. Impact on Success Criteria

* **SC-001 (Data Availability):** Ensures that the pipeline attempts to download from a valid, existing source.
* **SC-002 (Statistical Rigor):** Guarantees that the analysis is performed on the correct biological samples, preventing false negatives/positives due to mismatched metadata.
* **SC-003 (Biological Plausibility):** Ensures the resulting gene expression data is relevant to the specific thermal stress conditions defined in the hypothesis.

**Note:** This change does not alter the statistical methods or the definition of success, but rather ensures the input data matches the experimental design.

### 4. Implementation Details

* **Configuration Update:** The value `BIOPROJECT_ID` in `code/config.py` has been updated to `"PRJNA321023"` (Task T004c).
* **Code References:** All downstream tasks (T015, T018, etc.) will now reference this new ID.
* **Documentation:** This amendment record serves as the audit trail for the change.

### 5. Final Value Determination Date

The final value for the BioProject ID was determined and locked on **2023-10-27**. This value will remain constant for the duration of the current analysis pipeline (Phase 1-3) unless a formal new amendment is processed.

---

## Amendment ID: AMEND-002

**Date:** 2023-10-27
**Status:** Approved
**Author:** Automated Pipeline System (T004b)
**References:** T004, T009b

### 1. Description of Change

**Parameter:** `MIN_COUNT_THRESHOLD`
**Original Value:** Undefined / Placeholder
**New Value:** `10` (Provisional)

**Rationale:**
To satisfy Constitution Check VII (Uniform Filtering) and enable the execution of the initial pipeline run, a provisional numeric value is required. Empirical determination of the optimal threshold is deferred to the research phase (T009b).

### 2. Decision Process

* **Constraint:** The pipeline requires a numeric threshold to filter low-count genes before DGE analysis.
* **Strategy:** Adopt a standard, conservative provisional value (10 counts) to prevent the pipeline from failing due to missing configuration, while explicitly marking it as temporary.
* **Future Action:** The final threshold will be determined by analyzing the distribution of counts and variance in the real data (Task T009b) and updating `config.py` accordingly before the final production run (T020).

### 3. Impact on Success Criteria

* **SC-002:** Using a provisional value may introduce noise if the threshold is too low, or lose signal if too high. However, the "Fail Loudly" mechanism in downstream validation (T028b) will detect if the resulting statistical power is compromised, triggering a re-evaluation of this threshold.
* **Reproducibility:** The specific provisional value is documented here to ensure the initial run is reproducible.

### 4. Implementation Details

* **Configuration Update:** `MIN_COUNT_THRESHOLD = 10` is set in `code/config.py` with a comment referencing this amendment.
* **Documentation:** This record documents the provisional nature of the value.

---

*End of Amendments Document*