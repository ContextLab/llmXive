# Constitution of the llmXive Automated Science Pipeline

## Version 1.0

### Preamble
This document defines the immutable principles and governance structure for the
llmXive automated science pipeline. All research artifacts, data processing
steps, and statistical analyses must adhere to these principles.

---

## Core Principles

### Principle I: Reproducibility
Every experiment must be fully reproducible. Code, data, and configuration must
be version-controlled and accessible.

### Principle II: Transparency
All assumptions, data transformations, and statistical decisions must be
explicitly documented.

### Principle III: Data Integrity
Synthetic data is prohibited for final analysis. All datasets must be sourced
from verified, real-world repositories.

### Principle IV: Statistical Rigor
Statistical methods must be appropriate for the data distribution and research
question. P-values and confidence intervals must be reported with exact values.

### Principle V: Ethical Compliance
All data usage must comply with the original licenses of the source datasets.

### Principle VI: Statistical Methodology (Amended)
**Original Text**: "All correlation analyses must use Pearson correlation for
continuous variables and McNemar's test for paired categorical comparisons."

**Amended Text**: "All correlation analyses must use **Point-Biserial correlation**
for binary-vs-continuous comparisons and **Spearman rank correlation** for
non-normally distributed continuous variables. Paired comparisons of model
performance must use **Paired Permutation Tests** (10,000 permutations) rather
than parametric tests, to avoid assumptions of normality in performance metric
distributions."

**Rationale**: This amendment (AMEND-001-STATS) was ratified following the
submission of `methodology_rationale.md`. The original requirement for Pearson
and McNemar was found to be inappropriate for the specific nature of code
complexity metrics (often non-normal) and bug labels (binary). Point-Biserial
is the mathematically equivalent form of Pearson for binary variables but
explicitly acknowledges the binary nature of the target. Spearman is robust to
the skewed distributions common in software metrics. Paired Permutation Tests
provide a non-parametric alternative to t-tests for model comparison, ensuring
validity without normality assumptions.

---

## Amendment Process

Amendments to this constitution require:
1. A formal proposal document (`methodology_rationale.md`).
2. Scientific justification citing statistical theory or empirical evidence.
3. Ratification by the project lead or steering committee.
4. Update of this document with the new text and rationale.

---

## Governance

- **Project Lead**: Responsible for final ratification of amendments.
- **Steering Committee**: Reviews proposals for scientific validity.
- **Implementation Team**: Responsible for updating code to reflect ratified changes.

---

## History of Amendments

| ID | Date | Description | Status |
|----|------|-------------|--------|
| AMEND-001-STATS | 2024-05-15 | Update Principle VI to allow Point-Biserial, Spearman, and Paired Permutation Tests. | Ratified |

---

*This document is machine-readable and serves as the source of truth for statistical
configuration in the pipeline.*
