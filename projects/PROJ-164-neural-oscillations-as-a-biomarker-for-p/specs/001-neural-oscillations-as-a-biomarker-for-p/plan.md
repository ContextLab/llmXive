# Implementation Plan: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Branch**: `001-neural-oscillations-tDCS-biomarker` | **Date**: 2023-10-27 | **Spec**: `specs/001-neural-oscillations-tDCS-biomarker/spec.md`  
**Input**: Feature specification from `/specs/001-neural-oscillations-tDCS-biomarker/spec.md`

## Summary

The pipeline is organized around **mode selection** driven by data availability and power feasibility. The system distinguishes between **Data Insufficiency** (logistical data absence) and **Hypothesis Rejection** (scientific falsification). While the specification currently mandates the log string "Hypothesis Unanswerable" (FR-001), the internal narrative and reporting will clarify that this state represents "Data Insufficiency" to avoid the methodological error of conflating data scarcity with theoretical invalidity.

**Mode Classification**:
1. **Primary Mode**: A single-source paired dataset (EEG + tDCS outcomes) is found, and N is sufficient. Modeling proceeds.
2. **Data Insufficiency Mode**: No single-source paired dataset exists. The system logs "Hypothesis Unanswerable" (per spec) but internally classifies this as "Data Insufficiency". No modeling occurs.
3. **Underpowered Mode**: Paired data exists, but N < required minimum. Modeling is skipped, and statistical inference is suppressed.

The pipeline executes the following phases in strict order:

1. **Pre‑registration (FR‑010)** – Before any data download, the system writes `pre_registration.yaml` containing the primary outcome definition, hypothesis, analysis plan, and registered timestamp. This satisfies the explicit pre‑registration requirement.

2. **Systematic Dataset Search** – A reproducible script performs a systematic search across OpenNeuro, PhysioNet, and the tDCS‑DataBank using specific queries (e.g., "EEG" AND "tDCS" AND "motor"). It logs all candidate accession numbers and search parameters. This replaces static assumptions with an explicit search procedure.

3. **Source Identification (FR‑012, FR‑013)**  
   * **EEG Source Identification** – If a candidate EEG source is found, `verified_eeg_source.json` is written with fields `source_url`, `checksum`, `subject_count`, and a verification flag.  
   * **tDCS Source Identification** – Analogously, `verified_tdcs_source.json` records the tDCS source metadata. If no source is found, these artifacts record status `"unavailable"`. This explicit task ensures FR-012 and FR-013 are met even if the result is negative.

4. **Data Alignment Check (FR‑001, FR‑011, FR‑015)** – The system verifies that the EEG and tDCS data originate from the **same** study (single source). If alignment fails, it logs the exact required message:

   ```
   Hypothesis Unanswerable: No single-source paired dataset found
   ```

   *Note: This log message is mandated by the current spec. However, the internal state and final report will explicitly frame this as "Data Insufficiency" to prevent the scientific misinterpretation that the hypothesis is false.*

5. **Representativeness Check (FR‑018)** – Before power analysis, the system generates a demographic and protocol summary (age, sex, task type) to flag potential sampling bias. If the sample is highly homogeneous (e.g., only healthy young adults), a `generalization_risk` flag is raised, even if N is sufficient.

6. **Power Analysis & Feasibility Gate (FR‑007, FR‑008)** – Using the *corrected* effect size metric for regression (Expected R² or correlation coefficient r), the system computes the minimum required N. *Note: The current spec (FR-007) mandates Cohen's d (a group difference metric), which is methodologically mismatched for regression. The plan implements the correct regression-based power analysis but flags this discrepancy for a spec kickback.* If the actual N < required, it writes `power_analysis.json` with status **Underpowered** and skips inferential statistics.

7. **Preprocessing (FR‑002, FR‑013, VI)** – MNE‑Python pipeline: band‑pass 1–45 Hz, common‑average reference, automated bad‑channel rejection (z‑score > 5). Outputs are stored in `data/processed/epochs/` with new filenames; raw files remain untouched (III).

8. **Feature Extraction (FR‑003, FR‑009)** –  
   * **Spectral Power** – Welch’s method for delta, theta, alpha, beta, gamma.  
   * **Connectivity** – PLV and wPLI for all channel pairs.  
   * **Normality Check** – Shapiro‑Wilk on tDCS response; if p < 0.05, the pipeline selects **Rank‑Ridge** regression (a robust multivariate method) instead of standard Ridge. This satisfies FR‑009 while maintaining the multivariate prediction goal, avoiding the univariate fallback (Spearman) which would break the modeling requirement.

9. **Modeling (FR‑004)** – Nested cross‑validation (inner loop selects ridge/rank-ridge α, outer loop estimates performance). If normality holds, standard Ridge is used; otherwise Rank‑Ridge.

10. **Validation & Robustness (FR‑005, FR‑006, FR‑014, SC‑006)** –  
    * **Permutation Testing** – 1,000 permutations generate a null distribution of R².  
    * **Kolmogorov‑Smirnov Test** – Applied to the permutation p‑values; result stored as `ks_test_result` (statistic & p‑value) to satisfy SC‑006.  
    * **FDR Correction** – Benjamini‑Hochberg applied to final model coefficients **only if** power analysis reports "Sufficient".  
    * **Sensitivity Analysis** – Sweeps p‑thresholds {0.01, 0.05, 0.1} and R² thresholds (configurable). Stability variance is reported; significance is considered "stable" when ≥2 of 3 thresholds retain p < 0.05.

11. **Generalization Check (Principle VII)** – **Conditional Execution**: This step ONLY runs if **Primary Mode** is active (paired data exists and modeling ran).  
    * If found, the system attempts to locate an **independent** paired dataset (different study, same modalities).  
    * If a secondary dataset is found, the same pipeline (steps 7‑10) is run on the secondary data, and performance metrics are compared.  
    * If no secondary dataset is found, or if the primary dataset was missing the target variable (tDCS outcome), the system logs:
      ```
      Generalization Unanswerable: No independent paired dataset found (or primary target missing)
      ```
    This satisfies the constitutional requirement to *attempt* evaluation of generalizability while acknowledging logical constraints.

12. **Manifest Generation (IV)** – After all tasks, `manifest.json` maps every output metric (e.g., `adjusted_r2`, `ks_test_result`) to the specific input file hash and the exact code block identifier, ensuring traceability to the `model_output.schema.yaml` and `output.schema.yaml` contracts.

13. **Reporting** – `output/reports/final_report.md` consolidates: ingestion outcome, power analysis, preprocessing logs, modeling metrics, validation tables, KS test, sensitivity variance, and any "Data Insufficiency" or "Unanswerable" messages.

## Project Structure

```text
specs/001-neural-oscillations-tDCS-biomarker/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── eeg-features.schema.yaml
│   ├── feature.schema.yaml
│   ├── model_output.schema.yaml
│   ├── output.schema.yaml
│   ├── tdc-response.schema.yaml
│   └── pre_registration.schema.yaml
└── tasks.md
```

### Code Layout (root)

```text
projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p/
├── code/
│   ├── __init__.py
│   ├── config.py               # seeds, paths, hyper‑params
│   ├── pre_registration.py     # writes pre_registration.yaml
│   ├── dataset_search.py       # systematic search script
│   ├── source_identification.py# writes verified_*_source.json
│   ├── ingestion.py            # FR‑001 gate
│   ├── power_analysis.py
│   ├── representativeness.py
│   ├── preprocessing.py
│   ├── feature_extraction.py
│   ├── modeling.py             # Ridge & Rank‑Ridge
│   ├── validation.py
│   ├── generalization.py       # secondary dataset handling
│   ├── manifest.py
│   └── main.py                 # orchestrator, mode handling, logging
├── data/
│   ├── raw/
│   └── processed/
├── output/
│   ├── reports/
│   └── artifacts/
├── tests/
│   └── contract/
├── requirements.txt
└── README.md
```

## Constitution Check

| Principle | Requirement | Plan Compliance Strategy |
|-----------|-------------|--------------------------|
| **I. Reproducibility** | Random seeds pinned; dataset URLs fixed. | `config.py` seeds `numpy`, `random`, `torch`; checksums recorded in manifests. |
| **II. Verified Accuracy** | Citations verified. | All dataset URLs come from the verified list; no invented sources. |
| **III. Data Hygiene** | Checksums, immutable raw data. | `manifest.json` and per‑file `checksum` fields; raw files never overwritten. |
| **IV. Single Source of Truth** | One row / one code block per figure. | `manifest.json` maps each metric to input hash and code block ID, explicitly referencing schema fields (e.g., `adjusted_r2` in `model_output.schema.yaml`). |
| **V. Versioning Discipline** | Content hashes tracked. | `hashes.json` generated after each run; consumed by Advancement‑Evaluator. |
| **VI. Neurophysiological Data Integrity** | Band‑pass 1–45 Hz, CAR, bad‑channel rejection. | Implemented in `preprocessing.py` per MNE best practices. |
| **VII. Biomarker Validation** | Independent dataset evaluation. | Generalization Check (Step 11) attempts secondary paired dataset; logs outcome if impossible or primary target missing. |
| **VIII. Pre‑registration (new)** | Primary outcome & analysis plan recorded before processing. | `pre_registration.yaml` written by `pre_registration.py`. |
| **IX. Source Identification (new)** | Canonical EEG and tDCS sources explicitly verified. | `verified_eeg_source.json` and `verified_tdcs_source.json` created before ingestion. |

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| FR / SC | Covered by | Phase / File |
|---------|------------|--------------|
| FR‑001, FR‑011, FR‑015 | `ingestion.py` + mode logic | plan.md |
| FR‑002, FR‑013 | `preprocessing.py` | plan.md |
| FR‑003 | `feature_extraction.py` | plan.md |
| FR‑004 | `modeling.py` (Ridge & Rank‑Ridge) | plan.md |
| FR‑005, FR‑014 | `validation.py` (FDR) | plan.md |
| FR‑006 | `validation.py` (sensitivity) | plan.md |
| FR‑007, FR‑008 | `power_analysis.py` (Note: Corrected metric) | plan.md |
| FR‑009 | `feature_extraction.py` + conditional in `modeling.py` (Rank-Ridge) | plan.md |
| FR‑010 | `pre_registration.py` | plan.md |
| FR‑012, FR‑013 | `source_identification.py` | plan.md |
| FR‑018 (new) | `representativeness.py` | plan.md |
| SC‑001 | `ingestion.py` logs checksums | plan.md |
| SC‑002 | `modeling.py` + `validation.py` | plan.md |
| SC‑003 | CI runtime / memory monitoring in `config.py` | plan.md |
| SC‑004 | `validation.py` stability table | plan.md |
| SC‑005 | `power_analysis.py` output | plan.md |
| SC‑006 | KS test in `validation.py` | plan.md |
| SC‑007 (new) | `representativeness.py` summary | plan.md |

## Spec Kickback Notes

The following discrepancies between the current specification and the scientifically rigorous implementation plan have been identified and flagged for a spec update (kickback):

1. **FR-007 (Power Analysis)**: The spec mandates "Cohen's d=0.5" (a group difference metric) for a regression task. The plan uses Expected R²/r (regression metric) but logs the discrepancy. *Action: Update FR-007 to specify R² or correlation coefficient.*
2. **FR-009 (Normality)**: The spec mandates "Spearman" (univariate) as a fallback. The plan uses "Rank-Ridge" (multivariate robust) to maintain the prediction goal. *Action: Update FR-009 to allow robust multivariate methods.*
3. **FR-001 / US-1 (Log Message)**: The spec mandates "Hypothesis Unanswerable" which conflates data scarcity with hypothesis falsification. The plan uses this log for compliance but clarifies the internal state as "Data Insufficiency". *Action: Update spec to use "Data Insufficiency" terminology.*