---
action_items:
- id: 6aa90121e71f
  severity: science
  text: "The manuscript reports mean performance improvements but provides no measures\
    \ of variance (e.g., standard deviations, confidence intervals) or statistical\
    \ significance testing for the gains shown in Table\u202F1 and Table\u202F2. Add\
    \ appropriate significance analysis to substantiate that the reported ~3\u2013\
    8\u202F% improvements are robust and not due to random seed variability."
- id: 3dee7cdfe581
  severity: science
  text: "Branching Score (BS) is introduced as a product of normalized entropy and\
    \ a future\u2011value term (Eq.\u202F5). However, the paper lacks an ablation\
    \ that isolates the contribution of each component across a range of hyper\u2011\
    parameters (\u03B5, \u03B5\u2032, \u03B3, b). Include a systematic sensitivity\
    \ study to demonstrate that BS is not over\u2011fitted to the chosen settings."
- id: ef6602d27402
  severity: science
  text: The experimental section mentions training on 2 and 5 epochs for reasoning
    and search tasks respectively, but does not disclose the number of random seeds
    or repetitions used. Clarify the replication protocol (e.g., number of runs, seed
    variance) to ensure that results are not a product of a particular initialization.
- id: 14af0df16508
  severity: science
  text: "Multiple design choices (budget allocation N/B/L, clipping thresholds, KL\
    \ coefficient \u03B2) are explored in the appendix, yet the main text does not\
    \ discuss a correction for multiple hypothesis testing when selecting the best\
    \ configuration. Provide a discussion of how hyper\u2011parameter search was controlled\
    \ to avoid p\u2011hacking."
- id: 670cf2f5fcc9
  severity: science
  text: "The theoretical guarantees (Theorem\u202F1 and 2) assume monotonicity of\
    \ conditional reward variance with BS and bounded KL divergence, but no empirical\
    \ verification of these assumptions is presented. Include empirical checks (e.g.,\
    \ correlation between BS and observed variance) to support the applicability of\
    \ the theorems."
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:18:56.722511Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper introduces APPO, a novel agentic RL algorithm that shifts branching and credit assignment from coarse tool‑call units to fine‑grained “procedural” decision points. Empirically, the authors evaluate APPO on 13 benchmarks spanning mathematical reasoning, knowledge‑intensive QA, and deep‑search tasks, reporting consistent gains over strong baselines (e.g., Table 1 and Table 2). While the breadth of datasets is commendable, the evidence presented has several weaknesses that limit confidence in the claimed improvements.

First, the reported results are presented as point estimates (averages) without any indication of variability. The manuscript does not report standard deviations, confidence intervals, or perform statistical significance testing (e.g., paired t‑tests) for the differences between APPO and baselines. Given the modest absolute improvements (≈3–8 % on average), it is essential to demonstrate that these gains are statistically reliable and not artifacts of random seed selection or dataset sampling variance.

Second, the core contribution—the Branching Score (BS) in Eq. 5—is validated only through a few ablations (Table 3) that replace BS with raw entropy or remove the future‑aware advantage term. However, the sensitivity of BS to its constituent hyper‑parameters (ε, ε′, γ, the clipping range, and the weighting factor b) is not systematically explored. Without a broader hyper‑parameter sweep, it remains possible that the reported performance is contingent on a specific configuration rather than reflecting a robust methodological advantage.

Third, the experimental protocol lacks details on replication. The authors state that training proceeds for “2 epochs” (reasoning) and “5 epochs” (search) but do not disclose how many random seeds were used, whether results are averaged over multiple runs, or how variance across runs was handled. This omission hampers reproducibility and raises concerns about the stability of the reported gains.

Fourth, the paper conducts extensive architectural and budget‑allocation studies (e.g., Table 4, Appendix E) but does not discuss any correction for multiple comparisons. Selecting the best configuration after exploring many (N, B, L) settings without adjusting for multiple hypothesis testing can inflate the risk of false positives (p‑hacking).

Finally, the theoretical claims (Theorem 1 – variance reduction, Theorem 2 – policy improvement bound) rely on assumptions such as monotonicity of reward variance with BS and bounded KL divergence. No empirical evidence is provided to verify these assumptions (e.g., measuring the correlation between BS and observed conditional reward variance). Including such validation would strengthen the connection between theory and practice.

In summary, while APPO shows promising empirical trends, the current evidence base lacks rigorous statistical validation, comprehensive hyper‑parameter sensitivity analysis, and clear replication details. Addressing these issues will substantially increase confidence that the observed improvements are genuine and generalizable.
