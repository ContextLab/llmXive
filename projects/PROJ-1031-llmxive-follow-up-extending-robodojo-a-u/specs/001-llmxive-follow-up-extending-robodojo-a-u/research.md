# Research: Extending RoboDojo with Symbolic Abstractions

## Research Question
To what extent is high‑fidelity continuous physics simulation necessary for successful long‑horizon robot manipulation planning, and can topological symbolic abstractions alone suffice to bridge the sim‑to‑real gap in generalist policies?

## Dataset Strategy

| Dataset Name | Verified Source URL(s) | Role |
|--------------|------------------------|------|
| RoboDojo (parquet) | ` | Primary task specifications, video frames, ground‑truth trajectories. |
| RoboDojo Assets (BUILD_COMPLETE) | ` | Task metadata, success criteria (pose/orientation thresholds). |
| RoboDojo Deposit‑Coin Scene Info | ` | Additional validation of task graph structures. |

**Access Method**  
All three sources are public HuggingFace datasets. They are streamed with `datasets.load_dataset(..., streaming=True)` to keep RAM usage ≤ 6 GB. No gated data are required.

## Methodology Overview

### 1. Semantic Embedding Generation (FR‑001, FR‑002)
- **Model**: Frozen MobileViT (`transformers`), CPU‑only, int8‑quantized if needed.  
- **Process**: Sample frames from each RoboDojo video, pass through MobileViT → 512‑dim vector.  
- **Output**: `SemanticEmbedding` stored in `data/interim/semantic_embeddings.parquet`.  
- **Mapping Validation**: Compute precision/recall against a hand‑annotated ground‑truth of a representative set of tasks (FR‑013). Ambiguous cases trigger an `AmbiguousMapping` event, **but are retained** with a low‑confidence fallback mapping; `mapping_confidence` flag is stored for later covariate analysis (addresses Methodology‑13618854).

### 2. Symbolic State Construction (FR‑002, FR‑011)
- Convert embeddings to a `SymbolicState` graph (object affordances, connectivity).  
- Two graph granularities for ablation: **Full Affordance Graph** vs. **Simplified Connectivity Graph** (FR‑008).  
- Validation against schema `contracts/symbolic_state.schema.yaml`.

### 3. Symbolic Planning (FR‑003)
- **Algorithm**: Primary A* search; fallback MCTS (depth = 10, 500 simulations) **only when node count exceeds the same threshold for both graph types**, ensuring algorithmic consistency across the ablation (addresses Methodology‑e08dde2b).  
- **Constraint**: Must return a valid `ActionSequence` within 60 s per task (SC‑002).  
- Output stored in `data/interim/action_sequences.parquet` (validated by `action_sequence.schema.yaml`).

### 4. Execution & Failure Detection (FR‑004, FR‑006, FR‑010, FR‑012)
- **Oracle Executor** (`executor_oracle.py`): deterministic rule‑based graph matcher; no physics simulation (isolates planner correctness, satisfies Principle VI).  
- **Real‑World Executor** (`executor_real.py`): adapts pre‑trained RoboDojo low‑level controller via a Sim‑to‑Real fine‑tuning protocol using a small set of real‑world videos (FR‑009).  
- **Failure Detector** (`failure_detector.py`): logs step‑wise outcomes, labels `Planner Infeasibility` vs. `Controller Execution Failure`, attempts replanning from the last successful sub‑goal (FR‑012).  
- All logs written to `data/interim/execution_logs.parquet` (schema `execution_outcome.schema.yaml`).  
- **GPU Escape Hatch**: Baseline GPU metrics (cycles, memory, wall‑clock) are collected on a Kaggle free GPU using a **scaled‑down subset** (identical task set) to avoid hardware confound (addresses Methodology‑0a41a032).

### 5. Statistical Analysis (FR‑005, FR‑007, FR‑014, FR‑015, FR‑016, FR‑017)
- **Primary Test**: Exact McNemar test on paired binary success outcomes (Symbolic vs. Neural Policy) with α = 0.05 (source: Replication crisis, https://en.wikipedia.org/wiki/Replication_crisis, α = 0.05).  
- **Separate Oracle‑Only Comparison**: Run McNemar on Oracle‑only success rates for Symbolic and Neural policies to isolate the effect of topological abstraction from low‑level controller performance (addresses Scientific‑Soundness‑f2b226e5).  
- **Effect Size**: Odds‑ratio and rank‑biserial correlation (FR‑015).  
- **Compute Overhead**: Percentage reduction in CPU cycles, memory, and wall‑clock versus **GPU baseline** collected on Kaggle (FR‑007, FR‑017).  
- **Physics Fidelity Gap**: Oracle success – Real‑world success (FR‑010, SC‑006).  
- **Ablation Study**: Compare full vs. simplified graphs while keeping planner algorithm fixed (A*) and report success‑rate, compute‑overhead, catastrophic‑failure rate (FR‑008).  
- **Power Analysis**: Using the exact McNemar power formula (see Methodology‑73903e96), with N = 18 paired tasks, discordant‑pair proportion estimated from a Multi‑task pilot (`p_d ≈ 0.30`), we achieve ≥ 0.80 power to detect a medium effect size (Cohen’s h = 0.5). The calculation and assumptions are documented in the final report (FR‑014, SC‑012).  
- **Wilcoxon Test Citation**: *Wilcoxon, F. (1945). “Individual Comparisons by Ranking Methods”. **Biometrics**, 1(2), 80‑83. * (satisfies Principle II).  

## Decision Rationale
- **CPU‑only MobileViT** satisfies the CPU‑tractability requirement (US‑1).  
- **A\*** provides optimality for small graphs; **MCTS** offers robustness for larger graphs without changing the algorithm across ablation conditions.  
- **Oracle** eliminates physics confounds, fulfilling Principle VI.  
- **Exact McNemar** is appropriate for paired binary outcomes; the added Oracle‑only comparison isolates the planner effect.  
- **GPU baseline on Kaggle** removes the hardware confound while staying within the free‑tier compute budget.  
- **Power analysis** is explicitly calculated, avoiding optimistic claims.  

## Compute Feasibility (CPU‑First)
All components run on a 2‑core CPU, ≤ 6 GB RAM, ≤ 4 h total wall‑clock. The only GPU usage is the optional baseline collection on Kaggle, which is a small, scaled‑down run.

---



## References

- Replication crisis, α = 0.05. https://en.wikipedia.org/wiki/Replication_crisis  
- Wilcoxon, F. (1945). “Individual Comparisons by Ranking Methods”. *Biometrics*, 1(2), 80‑83. 
