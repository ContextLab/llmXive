---
action_items:
- id: f961f7ee65d6
  severity: science
  text: "Report per\u2011run variability (e.g., standard deviations or confidence\
    \ intervals) for the main ZPPO vs. baseline comparisons; currently only point\
    \ estimates are shown, which makes it hard to assess statistical significance\
    \ across random seeds."
- id: d3f991e457e6
  severity: science
  text: "Clarify the hyper\u2011parameter selection protocol (e.g., how replay fraction\
    \ \u03C1_replay=0.25 and augmentation fraction \u03C1_aug=0.25 were chosen) and\
    \ demonstrate that results are not overly sensitive to these choices."
- id: 49ddb891e7f8
  severity: science
  text: "Include an explicit held\u2011out benchmark set or cross\u2011validation\
    \ split to guard against over\u2011fitting to the 31 reported tasks; the current\
    \ evaluation uses the same suite for development and final reporting."
- id: 6abfa0b1b456
  severity: science
  text: "Provide a power analysis or justification for the sample size (31 benchmarks)\
    \ relative to the effect sizes reported (e.g., +7.5\u202Fpp macro\u2011average);\
    \ this will help readers gauge whether the observed gains are practically significant."
- id: b7ad362fb047
  severity: writing
  text: Add replication details such as random seed values, number of training runs
    per configuration, and hardware reproducibility notes to enable independent verification.
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:03:06.416688Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript introduces Zone of Proximal Policy Optimization (ZPPO) and reports impressive macro‑average gains (e.g., +7.5 pp over GRPO†) across 31 multimodal benchmarks. While the breadth of evaluation (LLM, VLM, Video) and the inclusion of multiple student scales (0.8 B–9 B) are strengths, the evidential foundation has several gaps.

1. **Sample size and statistical robustness** – The primary evidence consists of single‑run performance numbers per benchmark. Although the authors provide cluster‑bootstrap confidence intervals for pairwise deltas (Section § C.1), these intervals are derived from resampling benchmarks, not from repeated experimental runs. Consequently, they do not capture variability due to random initialization, data shuffling, or stochastic training dynamics. Reporting per‑run standard deviations or confidence intervals (e.g., across 3–5 seeds) would allow a more rigorous assessment of whether the observed improvements exceed random fluctuation.

2. **Control conditions and hyper‑parameter tuning** – ZPPO introduces several new components (BCQ, NCQ, replay buffer) and associated hyper‑parameters (ρ_replay, ρ_aug, buffer capacity). The paper presents ablations that isolate each component, yet the selection of the final hyper‑parameter values appears post‑hoc (“optimal” based on observed gains). A clearer description of the tuning protocol (grid search, validation set, early stopping) and sensitivity analyses (e.g., performance curves for varying ρ_replay) would reduce concerns about inadvertent over‑fitting to the benchmark suite.

3. **Effect size interpretation** – Gains of up to +9.3 pp for the 0.8 B VLM block are numerically large, but the absolute performance levels (e.g., from 41.0 % to 50.3 % VLM average) remain modest. A discussion of practical significance (e.g., how these gains translate to downstream tasks) and a power analysis justifying that 31 benchmarks are sufficient to detect the reported effect sizes would strengthen the claim of “substantial improvement.”

4. **Replication and reproducibility** – The paper lists extensive hyper‑parameters (Table § H) and compute costs, yet omits random seed specifications and the number of independent runs per configuration. Providing these details, along with a public script to reproduce at least one student scale, would enable the community to verify the robustness of ZPPO.

5. **Potential p‑hacking** – The extensive set of baselines (off‑policy distillation, on‑policy distillation, Hint, Prefix) and the many ablation tables raise the possibility of selective reporting. Explicitly stating that all evaluated configurations (including those that performed worse) are included in the appendix, and perhaps providing a summary table of all tried variants, would mitigate this risk.

Overall, the empirical evidence is promising but would benefit from additional statistical rigor, clearer hyper‑parameter selection methodology, and stronger reproducibility documentation. Addressing the action items above will substantially improve confidence in the central claims.
