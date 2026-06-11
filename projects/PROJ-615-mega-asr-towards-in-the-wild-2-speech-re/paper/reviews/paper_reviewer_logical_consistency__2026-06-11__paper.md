---
action_items:
- id: e236d3f73a46
  severity: science
  text: 'Hyperparameter contradiction: Section 4.1.2 and Analysis (Table hp-tau) claim
    tau=0.3 is optimal, but Appendix ''Reward tuning and diagnostics'' states tau=0.5
    was used. Reconcile the actual value used and update results accordingly.'
- id: e9333098a931
  severity: writing
  text: 'Abstract numerical mismatch: Abstract cites WERs (45.69% vs 54.01% on VOiCES;
    21.49% vs 29.34% on NOIZEUS) that do not match Tables 1 & 3 (7.35% vs 8.94%; 19.80%
    vs 23.97%). Verify and correct these values.'
- id: c9407ca60f79
  severity: writing
  text: 'Notation inconsistency: Equation 6 uses R_simple, while Section 4.1.1 defines
    R_static and Section 5 uses R_rule. Standardize reward notation throughout the
    manuscript.'
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:05:00.021237Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: full_revision
---

**Logical Consistency Review**

The paper presents a coherent methodology for robust ASR, but significant internal contradictions undermine the reproducibility and validity of the reported results.

**1. Hyperparameter Contradiction (Critical)**
The core reinforcement learning mechanism relies on a WER-gated threshold $\tau$. 
- **Section 4.1.2** explicitly states: "We set the three hyperparameters as $\tau = 0.3$".
- **Analysis Section (Table `tab:hp-tau`)** confirms $\tau=0.3$ yields the best WER (7.64) compared to 0.2, 0.4, and 0.5.
- **Appendix ("Reward tuning and diagnostics")** states: "Reward uses WER-gated dynamic reward with $\tau=0.5$".
This is a direct logical inconsistency. If the optimal value is 0.3 (as per the ablation study), using 0.5 in the final model (as per the appendix) contradicts the claimed optimization logic. If 0.3 was used, the appendix text is incorrect. This requires clarification and potentially re-running experiments to ensure the reported results match the described configuration.

**2. Numerical Discrepancies (Abstract vs. Results)**
The Abstract presents key metrics that do not align with the Results section tables:
- **Abstract**: Claims "45.69% vs. 54.01% on VOiCES R4-B-F" and "21.49% vs. 29.34% on NOIZEUS Sta-0".
- **Table 1 (NOIZEUS)**: Reports 19.80% (Mega-ASR) vs. 23.97% (Qwen3-ASR) for 0dB.
- **Table 3 (VOiCES)**: Reports 7.35% (Mega-ASR) vs. 8.94% (Qwen3-ASR) for Avg.
The Abstract numbers appear to be either decimal errors (e.g., 45.69% should be 4.57%) or refer to unstated subsets ("Sta-0"). Since these are the primary claims of the paper, they must match the detailed results tables to maintain logical consistency.

**3. Notation Inconsistency**
- **Equation 6** defines the final reward using $R_{simple}$.
- **Section 4.1.1** defines $R_{static}$ (Eq 3).
- **Section 5 (Implementation Details)** refers to $R_{rule}$.
While likely referring to the same component, inconsistent variable names ($R_{simple}$ vs $R_{static}$ vs $R_{rule}$) create ambiguity in the logical flow of the reward formulation.

**Recommendation**
The authors must resolve the $\tau$ value contradiction and align the Abstract numbers with the Tables. These are not merely stylistic issues but affect the scientific validity of the claims.
