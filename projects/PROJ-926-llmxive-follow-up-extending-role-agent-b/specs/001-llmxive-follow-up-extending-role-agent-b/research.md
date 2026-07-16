# Research: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

## Research Question

Can a lightweight, rule-based syntactic abstraction layer recover retrieval relevance and task completion rates in LLM agents after failure, when deep predictive modeling (World-in-Agent) is degraded to zero prediction horizon?

## Hypothesis

The syntactic abstraction intervention will significantly improve retrieval relevance scores and task completion rates compared to the degraded condition, approaching baseline performance levels, despite lacking deep predictive context.

## Methodological Rigor

### Experimental Design

**Design Type**: Between-Subjects (Independent Samples).  
**Total N**: 1500 unique task instances (500 per condition).  
**Randomization Protocol**: 
1.  Generate 1500 unique Task Instances (Task ID + Seed + Prompt Variation).
2.  Randomly assign each instance to exactly one of three conditions with equal probability:
    -   **Baseline**: Full WIA (prediction horizon > 0).
    -   **Degraded**: WIA prediction horizon = 0.
    -   **Intervention**: WIA prediction horizon = 0 + Syntactic Abstraction Parser active.
3.  Each condition generates its own independent set of failure trajectories. No trajectory is shared between conditions.

| Condition | Description | N | Expected Outcome |
|-----------|-------------|---|------------------|
| Baseline | Full WIA (prediction horizon >0); Llama-3-8B; failure trajectories generated | 500 | High retrieval relevance; high task completion |
| Degraded | WIA prediction horizon =0; Llama-3-8B; no predictive context | 500 | Low retrieval relevance; low task completion |
| Intervention | WIA=0 + Syntactic Abstraction Parser active during generation | 500 | Recovery in retrieval relevance; improved task completion |

**Ordering**:  
1. Data Generation (3 independent cohorts) → 2. Validation (ground-truth check) → 3. Retrieval Scoring (all conditions) → 4. Statistical Analysis (compare independent groups) → 5. Paper Generation (figures, stats).

### Dataset Strategy

| Dataset | Source | Access Method | Variables Needed | Fit Verification |
|---------|--------|---------------|------------------|------------------|
| ALFWorld Trajectories | NO verified source found (simulator-generated) | Programmatic simulation via `alfworld` Python package | Action logs, failure steps, ground-truth state transitions, task IDs | ALFWorld simulator is the source of truth; trajectories are generated on-the-fly; no external dataset required. |
| Frozen Task Bank | Internal (human-annotated) | Local JSON/Parquet file in `data/raw/task_bank.json` | Task IDs, root cause descriptions, ground-truth mappings | Task bank is derived from ALFWorld task definitions; human-annotated for ground-truth root causes; no external URL needed. |

**Dataset Rationale**: ALFWorld is a standard benchmark for embodied AI; the simulator provides deterministic state transitions and ground-truth failure modes. Since no external open dataset contains pre-generated failure trajectories with ground-truth labels, we generate them programmatically. The frozen task bank is internal and derived from ALFWorld task definitions, ensuring alignment with the simulator.

**Data Availability**: ALFWorld simulator is available via PyPI (`pip install alfworld`); no access-gated data; all data generated on-runner; no streaming required for <500 trajectories (fits in RAM).

### Computational Feasibility

**CPU-First Strategy**:  
- Llama-8B run in default precision (float32) on CPU; inference time on the order of seconds per trajectory; A large number of trajectories will be simulated over a period of –10 hours total.. *Optimization*: Use `torch.compile` or smaller batch sizes to stay within 6-hour limit; if exceeded, reduce N to a sample size determined by power analysis.  
- ALFWorld simulator runs in headless mode; no GPU required.  
- Statistical analysis (Shapiro-Wilk, t-test, Mann-Whitney U) via `scipy`; negligible compute.  
- Rule-based parser uses `re` module; negligible overhead.  
- Total estimated runtime: <6 hours (within limit).  

**GPU Escape Hatch**: Not needed; all methods are CPU-tractable. No transformer fine-tuning or diffusion models required.

### Statistical Rigor

- **Multiple Comparisons**: Three groups (Baseline, Degraded, Intervention); if >1 pairwise comparison, apply Bonferroni correction (α = 0.05/3 = 0.017).  
- **Power Analysis**: Target power ≥0.8; assumed medium effect size (Cohen's d=0.5); **N=1500 total (500 per group)** is sufficient for independent samples t-test (verified via `statsmodels` power analysis).  
- **Causal Inference**: Between-Subjects design with random assignment of task instances to conditions. Claims framed as causal regarding the *condition* (intervention vs. degraded) due to randomization.  
- **Measurement Validity**: Retrieval relevance score validated against ground-truth state transitions (simulator logs); syntactic abstraction validated against human-annotated task bank.  
- **Collinearity**: Predictors (syntactic patterns) are not definitionally related to outcomes; no collinearity expected; descriptive reporting of pattern frequencies.
- **Test Selection**: Independent samples t-test if Shapiro-Wilk p > 0.05; Mann-Whitney U if p < 0.05.

### Validation Independence & Circular Risk Mitigation

- **Ground-Truth Definition**: The 'ground-truth root cause' is defined as the **raw simulator state transition log** (e.g., `STATE: [object] not found`), which is generated by the simulator engine and is independent of the agent's text generation or internal predictions.
- **Retrieval Relevance Score**: Calculated as the semantic similarity between the **retrieved task definition** (from the Frozen Task Bank) and the **raw simulator state transition log** (ground-truth).
- **Predictor Independence**: The agent's failure log (used to generate the query for retrieval) is distinct from the ground-truth. The 'Baseline' condition uses WIA internal predictions to generate the query; the 'Degraded' condition uses raw logs; the 'Intervention' condition uses syntactic abstractions. The ground-truth (simulator log) remains the constant, independent target for all three conditions, preventing tautological advantage.

## Assumptions & Limitations

- ALFWorld simulator is deterministic and reproducible.  
- Llama-3-8B is available via PyPI and runs on CPU without quantization.  
- Ground-truth root causes are unambiguous and derivable from simulator logs.  
- Rule-based parser captures syntactic patterns with sufficient accuracy.  
- n=500 per group provides adequate power for medium effect sizes.  

**Limitations**:  
- No external validation of syntactic abstraction beyond retrieval relevance scores.  
- Simulated environment may not generalize to real-world robotics.  
- CPU-only execution may limit model size (no larger LLMs tested).