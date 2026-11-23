# Data Limitation Report: Experimental Onset Potentials

## Status: External Validation Data Not Found

**Generated**: Automatically by `code/reports/limitations_report.py`
**Trigger Condition**: `validation_mode = 'internal_fallback'` (see `data/validation/data_status.json`)

---

## Executive Summary

The automated search for **experimental onset potentials** required to validate the DFT and Machine Learning predictions for battery electrolyte decomposition (User Story 3) has failed to locate a suitable, programmatically accessible dataset. Consequently, the pipeline has proceeded in **Internal Validation Mode**, comparing model predictions solely against the held-out DFT dataset.

**Impact**: The model's accuracy against real-world experimental conditions remains unverified. The metrics reported (MAE, R²) reflect internal consistency with the training distribution, not experimental fidelity.

---

## Search Methodology

The following sources and methods were programmatically queried via `code/data/external_search.py` (Task T050):

1. **NOMAD API**:
 - **Query**: 'electrolyte', 'onset potential', 'cyclic voltammetry', 'EC', 'DMC', 'LiPF6'.
 - **Result**: No structured dataset containing explicit "onset potential" values linked to specific molecular IDs matching the project's DFT set was found. Data was either unstructured text or lacked the necessary experimental metadata.

2. **Materials Project Experimental Logs**:
 - **Query**: Battery electrolyte decomposition energies and potentials.
 - **Result**: The Materials Project primarily hosts DFT-calculated properties for solids. No experimental electrolyte onset potential datasets matching the specific molecular species (EC, DMC, LiPF6) were available via the public API.

3. **PubChem via `pubchempy`**:
 - **Query**: Molecular IDs for EC, DMC, LiPF6.
 - **Result**: Successfully retrieved molecular structures and basic properties. However, **experimental onset potentials** (electrochemical stability limits) are not standard fields in the PubChem public API response for these specific organic electrolytes.

4. **Literature DOI Check**:
 - **Source**: `docs/research.md` cited DOIs.
 - **Result**: The specific DOIs referenced in the research notes point to PDF publications. These documents were not parsed programmatically, and no machine-readable data repository link was found in the metadata.

---

## Detailed Findings

| Source | Status | Reason for Failure |
|:--- |:--- |:--- |
| NOMAD API | ❌ Failed | Data present is unstructured or lacks "onset potential" field. |
| Materials Project | ❌ Failed | Focus on solid-state DFT; no experimental electrolyte data. |
| PubChem | ❌ Failed | No experimental electrochemical stability data in API schema. |
| DOI Links | ⚠️ Skipped | PDFs not machine-readable; no data repository link found. |

---

## Consequences & Mitigation

### 1. Validation Mode Shift
As per the project's contingency logic (Task T051, T042), the system has automatically switched to `validation_mode = 'internal_fallback'`.
- **Action**: `code/models/evaluator.py` calculated metrics against the **Held-Out DFT Set** instead of an experimental set.
- **Warning**: Logs contain the message: *"External validation skipped: data not found; using internal fallback"*.

### 2. Reporting Limitations
The final `data/validation/validation_report.md` explicitly states:
> "External Validation: FAILED (Data Not Found). Metrics are based on internal DFT consistency."

### 3. Research Documentation Update
Per Task T053, `docs/research.md` has been updated to reflect this status, noting that the model's predictive capability for *real* battery performance is a hypothesis requiring future experimental validation.

---

## Recommendations for Future Work

1. **Manual Curation**: A domain expert should manually extract onset potential values from the cited literature (DOIs in `research.md`) and compile a CSV file at `data/external/experimental_onsets.csv`.
2. **API Integration**: Investigate if the NOMAD API supports a more specific query for "electrochemistry" or "liquid phase" data that was missed in the initial broad search.
3. **Data Sharing**: Contribute the resulting DFT-Experimental comparison dataset to the community once the manual curation is complete.

---

*This report was generated automatically by the llmXive pipeline upon failure of external data verification.*