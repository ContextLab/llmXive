# Research: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

## Research Question
Does ordering In-Context Learning (ICL) demonstrations by "Logical Difficulty" (derived from CoT DAG depth) improve accuracy and stability for non-reasoning models more significantly than **semantic curvature (SBERT-based)** or random ordering, and does this effect interact with model architecture type?

*Note: The original hypothesis focused on "geometry" problems. Due to dataset availability, this study focuses on "general logical dependency" in SFT traces.*

## Dataset Strategy

### Verified Sources
The following datasets are the **only** sources available per the verified list. The study must adapt to these or explicitly flag the mismatch.

| Dataset Name | Verified URL | Format | Relevance to Study |
|:--- |:--- |:--- |:--- |
| **DAG SFT** | ` | JSONL | Contains CoT-like chains. **Primary Candidate**. Used for DAG parsing and inference. |
| **TCS DAGs** | ` | Parquet | Theoretical CS graphs. **Not suitable** for CoT parsing. |
| **CS482 DAGster** | ` | Parquet | Workflow DAGs. **Not suitable** for CoT parsing. |
| **RBench** | ` | JSON | Config file only. **Not suitable**. |
| **DAG Word Freq** | ` | Parquet | Word frequencies. **Not suitable**. |

### Critical Mismatch & Mitigation (Generalized Validation)
- **Mismatch**: The spec requires "geometry and number theory" datasets with "explicit logical steps" and "external GeoQA difficulty ratings." The verified dataset `aaabiao/DAG_sft` is a general SFT dataset. It **does not** guarantee geometry-specific problems or human-validated expert difficulty ratings from GeoQA.
- **Mitigation (Generalized Validation)**:
 1. **Domain Shift**: The study will focus on "logical dependency in general reasoning" rather than geometry.
 2. **Validation Protocol**: Instead of external GeoQA ratings (unavailable), we will recruit **2 independent domain experts** to manually annotate a 50-sample subset of the SFT dataset for "Logical Complexity" (1-5 scale).
 3. **Metric Validation**: The "Logical Difficulty Score" (DAG depth) will be validated against these human ratings (target `r ≥ 0.6`). This provides external validity within the current domain, avoiding circularity.
 4. **Transparency**: The final report will explicitly state the domain shift and the use of generalized validation.

### Data Splitting Strategy (FR-006 Compliance)
To ensure the test set is distinct from the training/validation set:
1. **Full Dataset**: ~1000 traces.
2. **Split**:
 - **Gold Standard ([deferred])**: 50 traces reserved for **human expert annotation** (FR-007).
 - **Training/Validation ([deferred])**: 450 traces used for DAG construction, parser tuning, and prompt generation logic.
 - **Test Set ([deferred])**: 500 traces reserved **strictly for inference** and accuracy measurement. No DAG construction or prompt generation logic is tuned on this set.
3. **Implementation**: Random split with fixed seed (42).

### Data Loading
- **Loader**: `datasets.load_dataset("json", data_files="...")` for the JSONL file.
- **Preprocessing**: Filter for entries containing "thought" or "reasoning" fields. Extract problem statement and CoT trace.

## Methodology

### Phase 1: DAG Construction & Scoring (FR-001, FR-007)
1. **Parsing**: Use `networkx` to parse CoT traces.
 - **Rule**: Identify atomic steps (e.g., "Step 1:", "Therefore", "Thus").
 - **Dependency**: If Step B references a variable/concept from Step A, add edge A→B.
 - **Cycle Detection**: Reject if cycle length ≤ 5 or incoming edges > 3.
 - **Score**: `Logical Difficulty Score` = `max_path_length` (DAG depth).
2. **Validation (Generalized)**:
 - **Gold Standard**: 50 traces manually annotated by 2 independent experts for "Logical Complexity".
 - **Metric**: Pearson correlation (`r`) between DAG depth and Human Rating.
 - **Target**: `r ≥ 0.6`.
 - **Failure**: If `r < 0.6`, the "Logical Ascending" strategy is deemed invalid for this dataset, and the study proceeds to descriptive analysis only.

### Phase 2: Prompt Generation (FR-002)
1. **Strategies**:
 - **Logical Ascending**: Sort examples by `Logical Difficulty Score` (low to high).
 - **Logical Random**: Shuffle examples (fixed seed).
 - **Original CDS (SBERT)**: Sort by **Semantic Curvature** calculated using **Sentence-BERT (SBERT)**.
 - *Rationale*: SBERT captures semantic manifold geometry and word order, unlike TF-IDF (bag-of-words), providing a valid proxy for the original CDS hypothesis.
 - *Implementation*: Use `sentence-transformers/all-MiniLM-L6-v2` to embed traces, then calculate curvature based on embedding manifold geometry.
2. **Configuration**: 64-shot prompts. 10 random seeds.
3. **Output**: JSONL files for each (Strategy, Seed) combination.

### Phase 3: CPU-Only Inference (FR-003)
1. **Models**:
 - **Reasoning**: `Qwen2.5-7B-Instruct` (Quantized Q4_K_M).
 - **Non-Reasoning**: `Llama-3.1-8B-Instruct` (Quantized Q4_K_M).
 - **Constraint**: Use `llama-cpp-python` with `n_ctx=4096`, `n_gpu_layers=0` (CPU only).
2. **Execution**:
 - Run on GitHub Actions free runner (multi-core CPU, adequate RAM).
 - **Sampling**: To fit 6h limit, if full 360 runs exceed time, reduce to 5 seeds or 32-shot prompts (documented trade-off).
 - **Retry**: Max 2 retries per prompt on failure.

### Phase 4: Statistical Analysis (FR-004, FR-005)
1. **Metric**: Accuracy (binary: correct/incorrect) per prompt.
2. **Model**: **Linear Mixed-Effects Model (LMM)** (not ANOVA).
 - *Rationale*: ANOVA on n=10 seeds has critically low power. LMM uses individual trials (n=360+) with random effects for seeds, increasing power to detect interaction.
 - *Formula*: `Accuracy ~ Strategy * ModelType + (1 | Seed) + (1 | PromptID)`.
3. **Hypothesis**: Significant interaction term (`Strategy:ModelType`, p < 0.05).
4. **Correction**: Bonferroni correction for post-hoc pairwise comparisons (3 strategies × 2 models = 6 tests).
5. **Power**: Acknowledge power limitations but note LMM improves robustness over ANOVA.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied to all pairwise comparisons (FR-005).
- **Power**: LMM addresses the low power issue of n=10 seeds.
- **Causal Claims**: Observational study (ordering strategy). Claims will be framed as "associational" unless randomization of seeds is fully controlled (which it is, via fixed seeds).
- **Collinearity**: "Logical Depth" and "Semantic Curvature" may be correlated. If correlation > 0.7, report descriptive stats only; do not claim independent effects in regression.
- **Validity**: Parser validity is external (human experts). Domain validity is generalized (SFT vs. GeoQA).

## Compute Feasibility Check

- **RAM**: `Qwen2.5-7B` Q4_K_M requires ~5-6GB RAM. `Llama-3.1-8B` Q4_K_M requires ~6GB RAM. **Fits within 7GB limit.**
- **Disk**: 14GB limit. Several models (~6GB each) + data (~1GB) = ~13GB. **Tight but feasible.** Clean up intermediate files.
- **Time**: 360 runs × 30s/prompt = 180 mins. + overhead = ~3-4 hours. **Feasible.**

## References
- **DAG SFT Dataset**: `aaabiao/DAG_sft` (Verified URL).
- **llama.cpp**: CPU inference documentation.
- **LMM**: Standard statistical practice for small sample sizes (Pinheiro & Bates).
- **SBERT**: Reimers & Gurevych (2019).
