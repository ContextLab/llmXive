# Research: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

## Scientific Hypothesis

The capacity for faithful, context-grounded multi-hop reasoning in the OCC-RAG model is implemented via a sparse, localized sub-network of attention heads and feed-forward neurons, rather than a distributed mechanism across the full architecture.

## Dataset Strategy

| Dataset | Source | Usage | Verification Status |
|---------|--------|-------|---------------------|
| OCC-RAG Model Checkpoint | Original project repository (GitHub/Zenodo) | Frozen model for sensitivity analysis; base for pruning | NO verified source found (per task block); **manual fetch required**; if not provided, pipeline halts with 'DATA_UNAVAILABLE'. |
| Large-Scale Synthetic Multi-hop QA Corpus

The research question is to evaluate the effectiveness of multi-hop reasoning in large-scale synthetic QA datasets. The method involves generating a corpus of multi-hop questions and answers using a rule-based synthesis pipeline, following the approach described in (Author et al., 2023). | Original project repository (GitHub/Zenodo) | Sensitivity analysis (sampled), fine-tuning (a subset), test set | NO verified source found; **manual fetch required**; if not provided, pipeline halts with 'DATA_UNAVAILABLE'. |

**Critical Note**: Per the verified datasets block, **NO verified URL exists** for the OCC-RAG model or the synthetic corpus. The plan assumes these are available via the original project repository (GitHub/Zenodo) as stated in the spec's assumptions. **If unavailable, the project cannot proceed without manual data acquisition.** No URLs are fabricated.

## Methodology

### Phase 1: Gradient-Free Sensitivity Analysis (FR-001, FR-002)

1. **Masking Unit Definition**: The unit of analysis is **one attention head** or **one feed-forward neuron** (not individual weights). This avoids prohibitive cost and ensures structural interpretability.
2. **Masking Strategy**: **Independent Single-Unit Masking**. For each layer, mask exactly one head/neuron at a time. **Do NOT use sequential masking** (which conflates cumulative effects).
3. **Baseline Control**: For each masked unit, generate a distribution of **100 random subsets of the SAME SIZE** (i.e., 100 random heads/neurons).
4. **Metric Calculation**: Compute "Context Faithfulness Score" for the specific masked unit and the 100 random subsets.
5. **Sensitivity Score (Z-score)**: `Sensitivity = (Faithfulness_Baseline - Faithfulness_Masked_Specific) - Mean_Random) / Std_Random`. This isolates the specific unit's contribution against the distribution of random subsets of the same size, resolving the circular validation and size-mismatch concerns.
6. **Output**: CSV with columns `layer_id`, `param_id`, `sensitivity_score` (Z-score), `delta_faithfulness`, `random_baseline_mean`.

### Phase 2: Pruned Model Construction (FR-003)

1. **Selection**: Rank all parameters by sensitivity score (Z-score); retain top **[deferred]**.
2. **Pruning**: Set non-critical weights to zero; preserve architecture topology.
3. **Validation**: Ensure model remains compatible with standard inference engines.

### Phase 3: Lightweight Fine-Tuning (FR-004)

1. **Data**: A set of synthetic examples (sampled from a large corpus).
2. **Optimizer**: AdamW (CPU-compatible); low learning rate.
3. **Stopping**: Early stopping when gradient magnitude < 1e-4 for 3 consecutive epochs.
4. **Constraints**: Must complete within 4 hours on CPU; memory < 7 GB.
5. **Fine-Tuning Control**: **Run a parallel fine-tuning of the ORIGINAL (unpruned) model** on the same 10k examples. This distinguishes between "recovery of pruning damage" (pruned improves more) vs "general model improvement" (both improve similarly).

### Phase 4: Statistical Validation (FR-005, SC-002)

1. **Test 1 (Performance Preservation)**: Paired t-test on per-sample faithfulness scores (Original vs. Pruned). Threshold: p < 0.05 indicates significant drop.
2. **Test 2 (Sparse Core Validation)**: **Paired t-test comparing Sensitivity-Pruned vs. Random-Pruned** (same 50% retention). Threshold: p < 0.05 indicates Sensitivity-Pruned performs significantly better, supporting the "sparse core" hypothesis.
3. **Collinearity Check**: Pearson correlation between sensitivity scores and random subset must be < 0.2 (SC-005).
4. **Causal Identification Strategy**: The design is observational. Findings are framed as **associational**. The inclusion of the Random-Pruned control group strengthens the evidence for specific criticality, but causal claims (necessity) are limited without random assignment of parameters.

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (Limited CPU resources, 7 GB RAM, 14 GB disk, no GPU).
- **Memory Management**: 
  - **Layer-wise Loading**: Load the model layer-by-layer for masking to avoid loading the full large-scale weights simultaneously.
  - **Batched Inference**: Process samples in small batches to Keep activations under a manageable memory footprint..
  - **Sample 50k corpus** to fit RAM (e.g., 5k samples for sensitivity analysis).
  - Use CPU-only `torch` wheels; no CUDA dependencies.
  - Pruned model stored as sparse tensors to reduce memory.
- **Runtime**: 
  - Sensitivity analysis: ~ hours (sampled data, layer-wise).
  - Fine-tuning: ~ hours (10k examples, low epochs).
  - Total: < 6 hours.

## Decision Rationale

- **Why Independent Single-Unit Masking?**: Avoids the cumulative effects of sequential masking; isolates specific parameter contribution.
- **Why Z-score?**: Compares specific unit against a size-matched random distribution, resolving circular validation and size-mismatch concerns.
- **Why Sampling?**: Full 50k corpus may exceed 7 GB RAM; sampling ensures feasibility while preserving statistical validity.
- **Why Paired t-test?**: Controls for sample variance; directly tests performance preservation (SC-002).
- **Why Fine-Tuning Control?**: Distinguishes between pruning recovery and general improvement.
- **Why No Causal Claims?**: Observational design (no random assignment of parameters); findings framed as associational.

## Limitations & Edge Cases

- **Dataset Availability**: No verified URL for OCC-RAG model or corpus; project stalls if data unavailable (manual fetch required).
- **No Sparse Core**: If sensitivity delta < 0.01, flag as "no meaningful sparse core detected".
- **Pruning Failure**: If fine-tuning collapses model, log failure and report final score without recovery claim.
- **Architecture Incompatibility**: Pruning script must retain layer structure even with zero weights.