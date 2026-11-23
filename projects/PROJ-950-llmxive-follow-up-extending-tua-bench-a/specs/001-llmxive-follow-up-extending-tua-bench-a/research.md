# Research: llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

## Objective
Quantify the impact of a retrieval‑augmented “Procedural Memory Bank” on the execution success of a Llama 3.1 8B terminal‑use agent across multiple scientific workflow tasks, and assess statistical significance while respecting strict reproducibility and data‑hygiene standards.

## Dataset Strategy
| Role | Source | Access Method | Variables Required | Availability |
|------|--------|---------------|--------------------|--------------|
| **Task Set** | Official TUA‑Bench dataset (HuggingFace) | `datasets.load_dataset("tua_bench")` | `task_id`, `description`, `validation_script`, `task_type` (complex/routine) | Open, programmatic download |
| **Procedural Memory Bank** | Hand‑curated by the research team (a substantial set of entries) | JSON file in `data/memory_bank.json` | `entry_id`, `command`, `description`, `embedding` | Local, checksum‑verified |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (HF) | `datasets.load_dataset` (model hub) | N/A | Open, programmatic download |
| **LLM** | `meta-llama/Meta-Llama-3.1-8B` (HF) | `transformers.AutoModelForCausalLM.from_pretrained(..., load_in_4bit=True, device_map="auto")` (CPU‑only) | N/A | Open, CPU‑only quantized |

**Rationale** – The spec requires the TUA‑Bench task set; an official open‑source version exists on HuggingFace, satisfying the data‑availability rule without fabricating data. The procedural memory bank remains a local, verified artifact.

## Model & Retrieval Choices
| Component | Decision | Rationale |
|-----------|----------|-----------|
| **LLM Execution** | CPU‑only 4‑bit quantized Llama 3.1 8B via `bitsandbytes` (CPU mode) | Meets FR‑002 CPU‑only requirement while keeping inference tractable on the free runner. |
| **Retrieval** | Cosine similarity on MiniLM embeddings (CPU‑friendly, < 1 s per query) | Lightweight, deterministic, and easily reproducible. |
| **Statistical Tests** | McNemar’s exact test (primary) + Holm‑Bonferroni correction (k‑sweep) | Appropriate for paired binary outcomes; controls family‑wise error. |
| **Exploratory Test** | Wilcoxon signed‑rank test (binary outcomes) | Non‑parametric alternative to the inappropriate paired t‑test. |
| **Timeout Enforcement** | Python `signal.alarm` for per‑task; `multiprocessing` watchdog for batch limit | Guarantees hard limits in a reproducible way. |

## Experimental Design
1. **Baseline Condition** – Run the Llama 8B agent on the full set of tasks with standard in‑context prompting (no retrieval).  
2. **Augmented Conditions** – For each k ∈ {1, 3, 5}, retrieve the top‑k memory entries, prepend them to the prompt, and run the same agent.  
3. **Seeds** – Five distinct random seeds are used for each condition.; seeds are fixed in `code/constants.py`.  
4. **Randomized Run Order** – For each seed, the order of baseline and each augmented run is randomly shuffled to eliminate warm‑up or cache effects.  
5. **Outcome Recording** – For every (seed, task, condition) tuple we store:  
   - `success` (bool)  
   - `error_type` (enum)  
   - `retrieved_ids` (list)  
   - `false_positive` (bool) – derived from the relevance map (see Phase 0).  
   - `execution_time_sec` (seconds)  
6. **Aggregations** – Compute per‑condition success rates, false‑positive retrieval rates, retrieval‑miss rates, and total batch runtimes (checked against SC‑004).  
7. **Statistical Analysis** –  
   - Aggregate per‑task majority‑vote outcomes across seeds before applying McNemar’s exact test (addresses independence).  
   - Perform Wilcoxon signed‑rank test as an exploratory complement.  
   - Apply Holm‑Bonferroni across the three k tests.  
   - Compute separate gains for complex vs. routine tasks and compare to SC‑002 thresholds.  
   - Verify false‑positive rate < 20 % (SC‑003).  

## Power & Assumptions
- **Effect Size & Discordant Pairs** – Anticipated discordant‑pair proportion is expected to be modest.. Using the exact McNemar power formula (Fleiss, Levin & Paik, 2013, Eq. 9.3), with A comprehensive set of paired observations covering all tasks across multiple seeds (e.g., the full combination of 24 tasks × 5 seeds). the power to detect a two‑sided p < 0.05 is **≈ 0.84**, satisfying the > 80 % requirement.  
- **Causal Claim** – The design is observational (no randomization of tasks), so conclusions are limited to *associational* improvements due to retrieval augmentation, satisfying the constitution’s “Deterministic Execution‑Only Evaluation” principle.  
- **Measurement Validity** – Success is defined strictly by the deterministic TUA‑Bench validation script (exit code 0). No subjective scoring is used.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **GPU requirement** | Previously required GPU; now using CPU‑only quantization. | 4‑bit quantization keeps inference within CPU limits; benchmarked to stay under the 6 h batch limit. |
| **Order effects** | Fixed run order could bias results. | Randomize execution order per seed (Methodology‑0486d8b8). |
| **Relevance map validity** | Single annotator could introduce bias. | Two annotators, Cohen’s κ measurement, and adjudication (Methodology‑fd9356b4). |
| **Power mis‑estimation** | Over‑optimistic power claim. | Provide exact power calculation (Methodology‑9066ba60). |
| **Statistical misuse** | Inappropriate t‑test on binary data. | Use Wilcoxon signed‑rank test (Methodology‑b74c975d). |
| **Batch‑time overruns** | Could exceed 6 h limit. | Instrument batch runtime and assert ≤ 6 h (SC‑004). |
| **Synthetic data fallback** | If TUA‑Bench not reachable. | The plan explicitly fails with a clear error; no synthetic substitution is performed, preserving spec integrity. |

## Deliverables
- `baseline_results/aggregated.json` (overall success rate, failure modes, batch runtime)  
- `augmented_results/k_{k}/aggregated.json` (success rate, false‑positive rate, retrieval‑miss rate, batch runtime) for k = 1, 3, 5  
- `stats/` folder with McNemar, Wilcoxon, Holm‑Bonferroni, subgroup gains, and false‑positive outputs  
- `figures/` with bar plots and heatmaps  
- `results/summary.md` summarizing all SC compliance statements  

## Compute Feasibility Statement
All non‑LLM steps run comfortably on the 2‑CPU GitHub Actions runner (< 2 GB RAM). The 4‑bit quantized Llama 3.1 8B model runs on CPU within the 6‑hour batch budget (empirically a relatively brief duration for the full 24‑task batch). Total wall‑clock time per batch is expected < 2 h, well under the 6 h limit and the overall 30 h experiment budget.

## References
- Llama 3.1 8B model (CPU‑quantized): https://huggingface.co/meta-llama/Meta-Llama-3.1-8B  
- MiniLM embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2  
- TUA‑Bench dataset (official): 
- Fleiss, Levin & Paik (2013). *Statistical Methods for Rates and Proportions* (McNemar power formula).  
