# Spec Amendments for PROJ-079

This document records formal deviations from the original specification (`specs/001-predict-immune-response/spec.md`)
that are required to ensure computational feasibility, statistical validity, and adherence to the project's
hardware constraints (2-core CPU, limited RAM, no GPU).

## Amendment 1: Uniform Stability Proxy (T002b)

**Original Specification (FR-003):** Use ESM-1b (Evolutionary Scale Modeling) for predicted protein structural properties.

**Deviation:** ESM-1b requires significant GPU resources and memory that exceed the project's target runtime environment.
Instead, we implement the **Uniform Stability Proxy**, defined as the combination of:
1. Amino Acid Composition (AAC)
2. Hydrophobicity Scales (e.g., Kyte-Doolittle)

**Justification:** This proxy provides a robust, CPU-feasible approximation of protein stability and structural propensity
without requiring deep learning inference on large models. It is authorized by Task T002b.

**Impact:** All downstream tasks (e.g., T020) must use this proxy instead of ESM-1b.

---

## Amendment 2: Restricted k-mer Set (T002c)

**Original Specification (FR-003):** Extract k-mer frequencies for k = 3, 4, 5, 6.

**Deviation:** We restrict k-mer extraction to **k = 3 and k = 4 ONLY**.

**Justification:**
1. **Dimensionality Control:** Including k=5 and k=6 results in feature spaces of size $4^5=1024$ and $4^6=4096$ per sequence,
 leading to a total feature dimension that risks exceeding the sample size (N < 30) in the HDLSS (High Dimension, Low Sample Size) regime.
 This would invalidate the assumptions required for the Debiased Lasso (FR-012) and cause severe overfitting.
2. **CPU Feasibility:** Calculating and storing k=5,6 frequencies for a large corpus of viral genomes significantly increases
 runtime and memory usage, violating the 4-hour runtime constraint on a 2-core CPU.
3. **Biological Sufficiency:** k=3 (codons) and k=4 (tetramers) capture the majority of coding sequence bias and local structural signals
 relevant to immune recognition and host adaptation, as supported by prior literature on viral genomics.

**Impact:** All downstream tasks (e.g., T018c) must strictly limit k-mer extraction to k=3 and k=4.
This authorization is explicitly granted by Task T002c.

---

## Approval

These amendments are approved as part of the project's methodological adjustments to align with the Plan.md
technical context and hardware constraints.

- **Amendment 1 Approved:** T002b
- **Amendment 2 Approved:** T002c