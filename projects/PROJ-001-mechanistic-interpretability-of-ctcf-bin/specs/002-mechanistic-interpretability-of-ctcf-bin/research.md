# Research: Mechanistic Interpretability of CTCF Binding-Site Selection

## Dataset Strategy

**Status: BLOCKED**. The project cannot proceed to model training or interpretability analysis due to a fatal lack of verified data sources.

The specification (FR-001, US-1) requires the ingestion of ChIP-seq (CTCF), ATAC-seq, and histone modification (H3K27ac) data from ENCODE for at least 5 distinct cell types. The `# Verified datasets` block provided for this project contains the following:

| Dataset Name | Source URL (Verified) | Usage in Plan | Status |
|:--- |:--- |:--- |:--- |
| Human_DNA_v0 | ` | Sequence only (Material Cause) | **Verified** (but insufficient) |
| Human_DNA_v0_DNABert6tokenized | ` | Sequence only | **Verified** (but insufficient) |
| ATAC-seq | *None* | Required for "Formal Cause" (accessibility) | **NO VERIFIED SOURCE** |
| CTCF Peaks | *None* | Required for ground truth labels | **NO VERIFIED SOURCE** |
| H3K27ac | *None* | Required for chromatin context | **NO VERIFIED SOURCE** |

### Fatal Gap Analysis

1. **Missing Ground Truth (Labels)**: The spec requires a supervised model (FR-002) to predict CTCF binding. This requires a dataset with **verified binding labels** (e.g., ChIP-seq peaks). No such source exists in the verified block.
 * *Rejected Workaround*: Generating "synthetic labels" based on canonical motif scores creates a circular validation loop. The model would learn to predict the motif score, not biological binding. This fails to address the research question of finding "non-canonical" features (FR-003) because the target variable is definitionally determined by the canonical motif.

2. **Missing Chromatin Context (Formal Cause)**: The spec requires ATAC-seq and Histone data to distinguish between "motif present but inaccessible" and "motif present and accessible".
 * *Rejected Workaround*: Simulating chromatin signals is scientifically invalid and violates the Constitution (Principle VI: Biological Validity). The model cannot learn the "Formal Cause" without real data.

3. **Missing Multi-Modal Alignment**: Without verified ATAC/ChIP/Histone sources, it is impossible to align these modalities to genomic windows as required by US-1.

### Conclusion

The project **cannot proceed** to the training or interpretability phases. The "Sequence-Only" approach is rejected as it fundamentally fails to answer the research question (mechanistic interpretability of binding-site selection, which inherently involves chromatin context). The project is blocked until verified multi-modal datasets are identified.

## Statistical Rigor & Methodological Soundness

* **Multiple Comparisons**: N/A (No features identified).
* **Sample Size**: N/A (No dataset available). Power analysis cannot be performed because N is undefined.
* **Causal Inference**: N/A.
* **Collinearity**: N/A.
* **Measurement Validity**: N/A.

## Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Model**: N/A (Blocked).
* **Data**: N/A.
* **Runtime**: N/A.

## Risks & Mitigations

1. **Risk**: No verified source for CTCF labels.
 * **Mitigation**: **None**. The project cannot proceed.
2. **Risk**: No verified source for ATAC/Histone data.
 * **Mitigation**: **None**. The project cannot proceed.
3. **Risk**: CPU training too slow.
 * **Mitigation**: **None**. Training cannot start.

## Blocking Flaw Summary

The core scientific hypothesis—that non-canonical binding mechanisms exist and can be identified via SAE—requires a model trained on **real biological binding events** (labels) and **real chromatin context** (ATAC/Histone). Neither exists in the verified dataset sources. Attempting to use synthetic labels or sequence-only data would result in a tautological model that cannot distinguish between motif presence and binding, rendering the "interpretability" phase meaningless. The project must be halted or the scope revised to a problem solvable with available sequence data (e.g., motif discovery only, not binding prediction).