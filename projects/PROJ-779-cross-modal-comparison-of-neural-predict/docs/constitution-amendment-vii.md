# Constitution Amendment VII: Substitution of Behavioral Measures with Split-Half Reliability

## 1. Context and Authorization

This document serves as the formal draft of **Constitution Amendment VII**, proposed under the authority of the **Plan 'Constitution Check'** section of the `llmXive` research pipeline project **PROJ-779-cross-modal-comparison-of-neural-predict**.

The current Constitution of the project (Principle VII: Validation Independence) mandates that neural prediction error signals be validated against independent behavioral measures. However, the experimental design for this specific study utilizes **passive oddball paradigms** (datasets `ds000246` and `ds000117` from OpenNeuro), where subjects are instructed to ignore the stimuli (e.g., watching a silent movie or resting) to elicit automatic, pre-attentive mismatch negativity (MMN) responses. Consequently, **no concurrent behavioral performance data (accuracy, reaction time) exists** for the trials being analyzed.

Strict adherence to the original Principle VII would render the validation of these passive paradigms impossible, effectively blocking the scientific inquiry.

## 2. Justification for Amendment

### 2.1 The Problem of Passive Paradigms
In active oddball tasks, the "oddball" stimulus elicits a behavioral response (button press), providing a ground truth for validation. In passive paradigms:
- Subjects do not respond to stimuli.
- No reaction time or accuracy metrics are recorded.
- The "behavioral" measure is the mere presence of the evoked potential (MMN) itself, which creates a circular validation loop if used as its own validator.

### 2.2 The Proposed Proxy: Split-Half Reliability
To satisfy the spirit of **Validation Independence** (ensuring the signal is robust and not an artifact of noise or overfitting) without behavioral data, we propose substituting behavioral validation with **Split-Half Reliability**.

**Rationale:**
1. **Internal Consistency:** By splitting the trial set into two independent halves (e.g., odd vs. even trials) and computing the correlation of the resulting event-related potentials (ERPs) or source estimates, we verify that the signal is reproducible across independent samples of the same neural process.
2. **Noise Rejection:** Low reliability indicates that the observed "signal" is dominated by noise or non-stationary artifacts, failing the robustness check required by Principle VII.
3. **Scientific Precedent:** Split-half reliability (and Cronbach's alpha) is the standard psychometric method for validating internal consistency in ERP studies where external behavioral ground truth is unavailable.

## 3. Proposed Text Amendment

The following text is proposed to amend **Constitution Principle VII** for the duration and scope of Project PROJ-779:

> **Current Text (Principle VII):**
> "Neural prediction error signals must be validated against independent behavioral measures (e.g., reaction time, accuracy) to ensure the signal reflects a genuine cognitive process and not noise."
>
> **Amended Text (Principle VII - Passive Paradigm Exception):**
> "Neural prediction error signals must be validated against independent measures to ensure the signal reflects a genuine cognitive process and not noise.
>
> **Exception for Passive Paradigms:** In experimental designs where no concurrent behavioral data is available (e.g., passive oddball tasks), validation against independent behavioral measures shall be substituted with **Split-Half Reliability Analysis**.
>
> **Implementation Requirements:**
> 1. The dataset must be split into two independent halves (e.g., odd/even trials).
> 2. The correlation (or intraclass correlation) of the primary signal metric (e.g., MMN amplitude, source strength) between halves must exceed a threshold of **r ≥ 0.7** (or Cronbach's α ≥ 0.7).
> 3. The reliability score must be reported in the final results and used as the primary criterion for signal validity in lieu of behavioral metrics."

## 4. Implementation Plan

This amendment authorizes the implementation of the following tasks within the pipeline:
- **Data Splitting:** Logic to partition trials into odd/even sets without data leakage.
- **Reliability Calculation:** Implementation of split-half correlation and Cronbach's alpha in `code/validation/reliability.py`.
- **Threshold Enforcement:** Automated failure of the pipeline if reliability thresholds are not met (as per FR-013).
- **Reporting:** Inclusion of reliability metrics in the `data/results/final_report.md` under a dedicated "Constitution Compliance" section.

## 5. Governance Note

This document constitutes the **draft** amendment. Per project governance, this amendment must be reviewed and ratified by the **Advancement-Evaluator Agent** (via the Pull Request generated in Task T055b) before it becomes a binding rule for the remainder of the project execution. Once ratified, all subsequent analysis tasks will treat Split-Half Reliability as the authoritative validation metric for this project.

---
**Drafted By:** Automated Science Pipeline (llmXive)
**Date:** 2023-10-27
**Status:** Pending Ratification (T055b)