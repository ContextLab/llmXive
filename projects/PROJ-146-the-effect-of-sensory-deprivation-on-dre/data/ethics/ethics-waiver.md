# Ethics Waiver: Synthetic Data Usage Simulation Study

**Project ID**: PROJ-146-the-effect-of-sensory-deprivation-on-dre
**Study Title**: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)
**Date Issued**: 2023-10-27
**Status**: Active

## 1. Purpose of Waiver

This document serves as an ethics waiver and justification for the use of **synthetic data** in lieu of human subject data for the specific simulation study described in `data/protocols/protocol.yaml`.

The primary objective of this research phase is to validate the statistical analysis pipeline, including mixed-effects modeling, sensitivity analysis, and bootstrap robustness checks, under controlled ground-truth conditions (Positive, Null, and Negative effect scenarios).

## 2. Justification for Synthetic Data

According to the project design (`specs/001-sensory-deprivation-dreams`), human subject data collection involving sensory deprivation protocols requires:
- Extensive Institutional Review Board (IRB) approval.
- Informed consent from vulnerable populations.
- Strict safety monitoring during isolation periods.
- Significant time and resource overhead prior to pipeline validation.

To satisfy the requirement for **FR-004** (simulation parameters) and to enable rapid iteration on the analysis code (US1, US2, US3) without risking participant safety or violating privacy norms, this study utilizes a statistically generated dataset.

## 3. Data Generation Protocol

The synthetic data is generated programmatically by `code/generate_data.py` using the following constraints:
- **Source**: `data/protocols/protocol.yaml`
- **Sample Size**: N = 200 simulated participants.
- **Variables**: `condition` (strict, moderate, partial), `recall` (binary), `bizarreness` (ordinal 1-7).
- **Ground Truth**: Effect sizes are explicitly defined (d=0.5, d=0.0, d=-0.2) to allow for validation of statistical power and type I error rates.
- **Random Seed**: Pinned for reproducibility as per project constraints.

**No real human data is collected, stored, or processed in this phase.**

## 4. Ethical Compliance Statement

- **Human Subjects**: None involved.
- **Privacy**: No personally identifiable information (PII) is generated or used.
- **Safety**: No physical or psychological intervention is performed on living beings.
- **Transparency**: All data generation parameters are machine-readable and version-controlled in `data/protocols/protocol.yaml`.

## 5. Limitations and Future Work

Findings from this simulation study are strictly **associational** and **simulated**. They demonstrate the *capability* of the analysis pipeline to detect effects of specified magnitudes. They do not constitute clinical evidence of the effects of sensory deprivation on dreams.

Future work involving real human data will require a separate, full IRB submission and a new ethics approval document before data collection begins.

## 6. Approval

This waiver is approved for the duration of the simulation study phase (Phase 1 - Phase 3).

**Authorized By**: Automated Science Pipeline (ASPIRE) Implementation Agent
**Reference**: PROJ-146