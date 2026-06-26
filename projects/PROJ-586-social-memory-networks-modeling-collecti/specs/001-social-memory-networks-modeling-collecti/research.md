# Research: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

## Research Questions

1. **Primary**: Does context-window truncation degrade transactive-memory dynamics (specialization index, cue-retrieval efficiency) in multi-agent LLM systems?
2. **Secondary**: How do these metrics scale with the number of agents?
3. **Exploratory**: Do multi-agent collective remembering systems exhibit sublinear scaling laws analogous to urban infrastructure (characteristic scaling exponents)?

## Dataset Strategy

| Dataset | Purpose | Verified URL | Variable Fit Check |
|---------|---------|--------------|-------------------|
| MUST (parquet) | Primary dataset for agent interactions | | **MISMATCH**: Contains tool-calling data, not explicit game-state facts or cue annotations. Will require synthetic fact/cue generation (FR-011). |
| MUST-EN-ES (parquet) | Secondary dataset for cross-lingual robustness | | **MISMATCH**: Text-only, no game-state structure. Synthetic generator required. |
| USK-difficult (csv) | Benchmark dataset for retrieval tasks | https://huggingface.co/datasets/AMLGentex/us_100K_difficult/resolve/main/tx_log.csv | **PARTIAL**: Contains transaction logs; may have cue-like annotations but requires validation. Will use for construct validity comparison. |
| USK-easy (csv) | Benchmark dataset for retrieval tasks | https://huggingface.co/datasets/AMLGentex/us_100K_easy/resolve/main/tx_log.csv | **PARTIAL**: Same as above. Will use for construct validity comparison. |
| WINNIE-US2 (parquet) | Episode-level interaction data | https://huggingface.co/datasets/gimarchetti/winnie-us2/resolve/main/data/chunk-000/file-000.parquet | **PARTIAL**: Episode data may contain multi-agent interactions; cue annotations require validation. Will use for construct validity comparison. |
| USD-Enhanced (jsonl) | Prompt data for agent generation | https://huggingface.co/datasets/JasonXF/US3D-Enhanced/resolve/main/prompt.json | **PARTIAL**: Prompt data may serve as synthetic cue source. |
| Hanabi | Spec-required game environment | **NO VERIFIED SOURCE** | **MISMATCH**: Spec requires Hanabi, but no verified URL exists. Will use synthetic game-state generator. |
| CoQA | Spec-required dialogue dataset | **NO VERIFIED SOURCE** | **MISMATCH**: Spec requires CoQA, but no verified URL exists. Will use synthetic cue generator. |

**Decision**: Given the dataset-variable fit gaps, the implementation will:
1. Load from verified URLs where possible (US-1, US-2, US-3 sources)
2. For any dataset lacking explicit cue annotations or game-state facts, invoke the synthetic cue generator (FR-011) with minimum 10 synthetic cues per game
3. Document all dataset transformations with checksums and derivation notes (Constitution Principle III)
4. **Validation Step**: Compare synthetic-generated metrics against any available real multi-agent interaction data from US-100K and WINNIE-US2 datasets to assess construct validity. Document external validity limitations explicitly.

## Statistical Rigor

### Multiple Comparison Correction
- **Method**: Bonferroni correction for all family-wise hypothesis tests (FR-007)
- **Rationale**: Separate ANOVAs for specialization and retrieval efficiency plus sensitivity analysis across 3 thresholds requires correction
- **Corrected α**: α_corrected = 0.05 / k (k = number of tests)

### Power Analysis
- **Planned**: N = 500 games per condition (reduced for CPU feasibility), α = 0.05, power = 0.80 (FR-009)
- **Limitation Acknowledgement**: If estimated power < 0.70, report "Power limitation" flag (SC-004)
- **Effect Size**: [deferred] — will be computed post-hoc from pilot run

### Causal Inference Assumptions
- **Experimental Manipulation**: Context condition (full vs. limited) is experimentally manipulated within the simulation, supporting causal claims about context effects on transactive-memory metrics **within the simulated environment**
- **Internal Validity**: Random seed (42) and controlled agent instantiation provide internal validity for within-study comparisons
- **External Validity Caveat**: Claims are framed as associational for real-world generalization; simulation results apply to the multi-agent LLM framework, not biological memory systems
- **Identification Strategy**: Controlled manipulation of context window size provides causal identification for simulation effects

### Measurement Validity
- **Specialization Index**: Distribution-based metric of per-agent fact-contribution; bounded 0 to log₂(N_agents) (FR-004)
- **Cue-Retrieval Efficiency**: Proportion of successful fact-retrieval queries vs. uniform chance baseline (1/N_agents) (FR-005)
- **Baseline Justification**: The 1/N_agents baseline represents the null hypothesis of uniform random retrieval (no specialization). Improvement over this baseline indicates emergent transactive-memory structure, consistent with transactive-memory theory predictions of non-uniform distribution
- **Validation Evidence**: Metrics follow established transactive-memory theory (per spec); code version-controlled and deterministic (Constitution Principle VI)
- **Construct Validity**: Synthetic-generated metrics will be compared against real multi-agent interaction data where available to assess validity

### Predictor Collinearity
- **Acknowledgement**: Specialization index and retrieval efficiency may be definitionally related (both derived from fact-contribution distributions)
- **Analysis Approach**: Run **separate ANOVAs** for each metric rather than treating Metric as a between-subjects factor. This avoids circular validation where metrics are not empirically independent
- **Correlation Check**: Compute correlation between specialization and retrieval metrics to assess interdependence; report descriptively without claiming independent effects

## Computational Constraints & Method Selection

| Method | CPU-Feasible? | Justification |
|--------|---------------|---------------|
| Decoder-only LLM inference (transformers) | YES | Small models (e.g., distilgpt2, gpt2) with CPU wheel; default float32 precision |
| Separate ANOVA per metric (scikit-learn / statsmodels) | YES | CPU-tractable; no GPU requirements |
| Power-law fitting (scipy.optimize) | YES | CPU-tractable; 3 data points acknowledged as underpowered (US-3) |
| Synthetic cue generation | YES | Rule-based; no model inference required |

**Decision**: All methods selected are CPU-tractable and compatible with GitHub Actions free-tier (2 CPU, ~7 GB RAM, ≤6 h). No GPU, CUDA, or quantization methods are used.

## Reviewer Feedback Integration

| Reviewer | Suggestion | Implementation |
|----------|------------|----------------|
| geoffrey-west-simulated | Scaling analysis for memory accuracy/retrieval speed vs. agent count | Phase 7: Scaling analysis with power-law fitting as descriptive only; 95% CI reported; sublinearity note included; framed as exploratory trend analysis due to 3 data points limitation |
| david-krakauer-simulated | Memory as adaptation; forgetting critical | Note in future work; current scope focuses on remembering fidelity (per spec) |
| eric-kandel-simulated | Computational equivalent of CREB-mediated transcription | Note in future work; current scope focuses on transactive-memory metrics (per spec) |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dataset lacks required variables | HIGH | HIGH | Synthetic cue/fact generator (FR-011); document all transformations; validate against real multi-agent data |
| Runtime exceeds 6 h | MEDIUM | HIGH | Reduce game count to 500 per condition; sample dataset; batch processing; monitor with experiment.log (FR-010) |
| Memory buffer exceeds 7 GB | MEDIUM | HIGH | Queue-based serialization (FR-012); log conflict events |
| Power < 0.70 | MEDIUM | LOW | Report "Power limitation" flag (FR-009, SC-004); acknowledge in paper |
| No verified Hanabi/CoQA source | HIGH | MEDIUM | Synthetic game-state generator; document gap in paper; validate against real multi-agent data |
| Metrics not empirically independent | HIGH | MEDIUM | Separate ANOVAs per metric; correlation check; report descriptively |
| Synthetic data construct validity | HIGH | HIGH | Validate against US-100K and WINNIE-US2 real interaction data; document external validity limitations |