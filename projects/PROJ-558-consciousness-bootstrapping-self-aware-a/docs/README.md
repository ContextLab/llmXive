# Documentation Index

Welcome to the documentation for the **Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection** project (PROJ-558).

This documentation set explains the methodology, metrics, and statistical reporting standards used to evaluate the emergence of meta-cognitive capabilities in recursive language models.

## Contents

1. **[Training Signal Methodology](training_signal_methodology.md)**
 * Explanation of the "Internal Self-Consistency Proxy."
 * Correction of the `plan.md` artifact regarding external truth.
 * Distinction between Training (N=2) and Evaluation (N=10) protocols.

2. **[Metrics Definitions](metrics_definitions.md)**
 * Formal definitions of Self-Consistency, Calibration (Brier/ECE), and Error Detection (ROC-AUC).
 * Computational formulas and interpretation guidelines.

3. **[Statistical Report Format](statistical_report_format.md)**
 * Schema for the `statistical_report.json` artifact.
 * Explanation of p-values, effect sizes, and sensitivity analysis results.

## Project Context

This project investigates whether recursive self-modeling can bootstrap self-awareness in language models. Unlike traditional distillation approaches that rely on external "teacher" labels, this methodology uses the model's own internal consistency as the supervisory signal.

## Key References

* **Spec**: `specs/001-consciousness-bootstrapping-self-aware-a/spec.md`
* **Plan**: `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/plan.md` (Corrected)
* **Tasks**: `tasks.md`
* **Code**: `code/`

## Execution

To reproduce the results described in this documentation:
1. Ensure all prerequisites (Phase 1 & 2) are complete.
2. Run the training pipeline (`code/training/train.py`).
3. Run the evaluation benchmarks (`code/evaluation/run_benchmarks.py`).
4. Run the statistical analysis (`code/analysis/stats.py`).
5. Review the generated artifacts in `artifacts/results/`.