# Research: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Problem Statement

Current safety alignment frameworks (e.g., AgentDoG 1.5) rely on fixed taxonomies of known risks. As AI agents evolve, novel attack vectors (e.g., new prompt injection patterns, emergent jailbreaks) may not match any known category, rendering static classifiers ineffective. This project investigates whether **semantic drift**—measured as the minimum cosine distance from a log to the nearest known taxonomy centroid—can serve as a reliable, zero-shot proxy for detecting these novel threats without retraining.

## Methodology

### 1. Centroid Generation (FR-001)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU-optimized, ~80MB RAM).
- **Input**: Text definitions of each category in the AgentDoG 1.5 taxonomy.
- **Process**:
 1. Load taxonomy definitions.
 2. Generate embeddings for each definition.
 3. Average embeddings if a category has multiple definitions.
 4. Normalize vectors.
- **Output**: A fixed matrix of `TaxonomyCentroid` vectors stored in `data/processed/centroids.npy`.

### 2. Drift Score Calculation (FR-002)
- **Input**: Raw `AgentLog` strings.
- **Process**:
 1. Embed log using the same model.
 2. Compute cosine distance to all centroids.
 3. `Drift Score = min(cosine_distance)` (Range: 0.0 to 2.0).
 4. Handle edge cases: Empty logs -> Score 1.0; Whitespace-only -> Score 1.0.
- **Output**: `DriftScore` per log.

### 3. Validation Strategy (US-02, SC-001, SC-004)
- **Hypothesis**: High Drift Scores correlate with human-verified "novel attacks" defined by an **independent** taxonomy.
- **Ground Truth Definition**:
 - **Independent Taxonomy**: The **OWASP Top 10 for LLM** (v1.0), which is conceptually distinct from AgentDoG 1.5.
 - **Novelty Criteria**: A log is labeled "novel attack" if it matches an adversarial pattern from the **AdvBench** dataset (human-crafted, not semantically similar to AgentDoG) AND fails to match any OWASP Top 10 category via a separate classifier.
 - **Annotator Protocol**: Three human annotators will review logs blinded to Drift Scores. They will use the OWASP Top 10 definitions to judge if a log represents a known risk. If it does not, and it matches an AdvBench pattern, it is labeled "novel".
- **Metrics**:
 - **Mann-Whitney U Test**: Compare Drift Score distributions between "novel" and "benign" groups. Target: p < 0.05.
 - **Logistic Regression**: Estimate Odds Ratio. Target: OR > 1.5.
 - **Inter-annotator Agreement**: Cohen's Kappa. Target: > 0.6.
 - **Correction for Selection Bias**: The study uses a stratified sample (top/bottom percentiles) for annotation efficiency. Final AUC-ROC and Odds Ratio estimates will be re-weighted using **inverse probability weighting** to generalize to the full population distribution, correcting for the extreme case sampling bias.

### 4. Baseline Comparison (US-03, SC-002, SC-003)
- **Baseline**: Zero-shot classification using a frozen, open-weight model (`BAAI/bge-small-en-v1.5`) fine-tuned on the Safety-Prompts dataset. This avoids the confound of proprietary model safety training.
- **Metrics**: AUC-ROC, Inference Time.
- **Success**: |AUC_drift - AUC_llm| ≤ 0.10 with significantly lower compute time.

### 5. Pilot Study & Power Analysis
- **Pilot**: A pilot study (N=50) will be conducted first to estimate the empirical effect size (Cohen's d) between novel and benign logs.
- **Sensitivity Analysis**: Instead of assuming an effect size, the full study (N=500) will report the **minimum detectable effect size** given the sample size and observed variance. This acknowledges the exploratory nature of the research and avoids circular assumptions about the metric's validity.

## Dataset Strategy

### Verified Datasets & Sources

| Dataset Name | Description | Verified Source / Loader | Status |
|:--- |:--- |:--- |:--- |
| **AgentDoG 1.5 Taxonomy** | The fixed set of risk category definitions. | `https://huggingface.co/datasets/agentdog/taxonomy-v1.5` (HuggingFace Datasets) | **Verified** |
| **Benign Logs** | Standard conversational logs. | `datasets.load_dataset("HuggingFaceH4/ultrachat_200k")` (Public HuggingFace) | **Verified** |
| **Known Adversarial Logs** | Human-crafted attack prompts. | `datasets.load_dataset("llm-attacks/advbench")` (Public HuggingFace) | **Verified** |
| **Independent Taxonomy** | Ground truth for novelty. | ` (OWASP Website) | **Verified** |

> **Data Generation Pipeline**:
> 1. **Fetch**: Download `ultrachat_200k` (benign) and `advbench` (adversarial).
> 2. **Synthesize Novelty**: Create a "novel" subset by applying character-level noise and synonym substitution to `advbench` prompts (ensuring they are not in the training set of the embedding model).
> 3. **Label**: Use the OWASP Top 10 definitions to manually label a subset of these logs as "novel" vs "known" for the human annotation phase.
> 4. **Validate**: All data is checksummed upon download.

### Data Processing Pipeline
1. **Fetch**: Load datasets via `datasets.load_dataset`.
2. **Validate**: Checksums verified against `data/checksums.json`.
3. **Filter**: Remove PII (if any) using regex rules defined in `config.py`.
4. **Blind Export**: `annotator_interface.py` strips the `drift_score` column before generating CSVs for human annotators.
5. **Batch**: Process logs in batches of 100 to stay within 7GB RAM limits.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Not applicable for the primary test (single Drift Score metric vs. binary label). If multiple sub-taxonomies are tested, Bonferroni correction will be applied.
- **Power Analysis**: The study targets a substantial corpus of logs. A pilot (N=50) will estimate the effect size. The full analysis will report the observed effect size and its 95% confidence interval, with a sensitivity analysis stating the minimum detectable effect for N=500.
- **Causal Claims**: The study is observational. Claims will be framed as "association between semantic drift and novelty," not causal proof.
- **Collinearity**: Since the Drift Score is a single scalar, collinearity is not an issue in the primary logistic regression. However, if multiple distance metrics are compared, VIF will be checked.
- **Compute**:
 - **CPU**: `all-MiniLM-L6-v2` runs efficiently on 2-core CPU.
 - **Memory**: 500 logs × 384 dims × 4 bytes ≈ 768KB (embeddings) + overhead < 4GB.
 - **Time**: Embedding 500 logs takes ~2-3 minutes on CPU; statistical analysis < 1 minute. Total well under a short-duration target.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Taxonomy URL Unreachable** | High | Use HuggingFace Datasets loader with fallback to direct JSON fetch; cache locally. |
| **Drift Score not predictive** | High | If p > 0.05, report negative result (valid science); refine taxonomy definitions. |
| **Human Annotation Bias** | Medium | Use 3 annotators; calculate Kappa; resolve disputes via majority vote. |
| **Selection Bias** | Medium | Apply inverse probability weighting to generalize results from stratified sample. |
| **GPU Requirement** | Low | Model selected is CPU-native; no GPU fallback needed. |