---
action_items:
- id: ca36480658e5
  severity: science
  text: "Run each experimental configuration (e.g., 1B, 3B, 11B scales with different\
    \ optimizers) with at least three independent random seeds and report mean\u202F\
    \xB1\u202Fstandard deviation for pre\u2011training loss, perplexity, and downstream\
    \ accuracy. This will allow assessment of variance and statistical significance\
    \ of the reported gains."
- id: b954add1d601
  severity: science
  text: "Add statistical tests (e.g., paired t\u2011tests or bootstrap confidence\
    \ intervals) when comparing MoE with and without MPI on downstream benchmarks.\
    \ Include effect\u2011size metrics (Cohen\u2019s d or relative improvement %)\
    \ to quantify the practical relevance of the observed differences."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:39:12.851313Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript proposes a router redesign for Mixture‑of‑Experts (MoE) models based on a single‑step power‑iteration followed by L₂‑retraction (MPI). While the idea is mathematically motivated, the empirical evidence presented suffers from several methodological gaps that limit confidence in the central claims.

**Sample size and replication.** All reported results (Figures 1‑4, Tables 1‑5) stem from a single training run per configuration. The pre‑training token counts (e.g., 100 B tokens for 1 B models, 350 B tokens for 3 B/11 B models) are massive, but without multiple random seeds the variability of these large‑scale experiments remains unknown. Consequently, it is impossible to determine whether the modest loss reductions (≈0.013 pts) or downstream accuracy gains (≈1–2 % absolute) are statistically reliable or could be attributed to stochastic training fluctuations.

**Controls and baselines.** The paper compares MPI‑augmented MoE against a “vanilla” MoE baseline but does not include alternative router modifications (e.g., auxiliary loss, bias calibration) as controls. Moreover, the ablation study isolates power‑iteration and retraction, yet the presented plots lack error bars, making it unclear whether the observed degradations when removing retraction are significant.

**Effect sizes and statistical significance.** Improvements are reported as raw differences without confidence intervals or hypothesis‑testing. For downstream benchmarks, the average accuracy increase from 42.26 % to 43.93 % (≈1.7 % absolute) could be within the noise floor of the evaluation suite, especially given the 25‑task average. Reporting standard deviations across seeds or bootstrap confidence intervals would clarify whether these gains are practically meaningful.

**Potential p‑hacking.** The authors performed extensive hyper‑parameter sweeps (e.g., constant C′ in {1,2,4,8}) and selected the best performing setting for large‑scale runs. Without a pre‑registered protocol or correction for multiple comparisons, there is a risk of over‑fitting to the validation set. Explicitly stating how many configurations were tried and providing a validation‑test split would mitigate this concern.

**Robustness to alternative settings.** The paper claims optimizer‑agnostic benefits, yet only two optimizers (AdamW, Muon) and their hyperball variants are examined, each with a single seed. Demonstrating that MPI’s gains persist across different learning‑rate schedules, batch sizes, or expert counts (beyond the 64→256 scaling) would strengthen the robustness claim.

**Recommendations.** To solidify the empirical claims, the authors should (1) repeat each experiment with multiple seeds and report variability; (2) include statistical significance testing and effect‑size measures; (3) broaden the set of control baselines; and (4) disclose the full hyper‑parameter search space to address potential p‑hacking. Addressing these points will make the evidence base rigorous enough for acceptance.
