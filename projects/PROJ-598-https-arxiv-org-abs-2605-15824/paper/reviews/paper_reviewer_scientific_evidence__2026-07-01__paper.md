---
action_items:
- id: bf76f4be479d
  severity: science
  text: The claim of 23.8 FPS on an H200 GPU (Table 1) lacks necessary context regarding
    batch size, resolution, and chunk size. The baseline comparisons (0.13-0.77 FPS)
    do not specify if they were run under identical hardware or configuration constraints.
    Re-run baselines on the same H200 with identical settings or explicitly state
    the hardware differences to validate the 30-180x speedup claim.
- id: 1a4c1ec728c3
  severity: science
  text: The garment consistency metrics (HGC, LGC, NTP) rely entirely on Gemini-3.0
    scoring (Appendix). No inter-rater reliability, human correlation study, or ground-truth
    validation is provided for this LLM-as-a-judge approach. Without a correlation
    coefficient against human annotations, the quantitative superiority claims in
    Table 1 are scientifically weak.
- id: 0ab7b2b67d97
  severity: science
  text: The ablation study for Gradient-Reweighted DMD (Table 2) shows a significant
    drop in Amplitude (0.8395 vs 0.5106) when changing tau from 0.2 to 0.3, yet the
    text only claims 'best overall performance' without statistical significance testing
    or error bars. Provide standard deviations over multiple seeds to confirm these
    differences are not due to random variance.
- id: 395dad2a27d8
  severity: science
  text: The dataset size (62K triplets) is not compared against the scale of training
    data used by the baselines (e.g., VACE, Kaleido). If baselines were trained on
    significantly larger datasets, the performance gap might be attributed to data
    scale rather than the proposed architecture. Clarify the data scale of all baselines.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:11:36.706115Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel framework for interactive garment customization, but the scientific evidence supporting the quantitative claims requires strengthening.

First, the primary efficiency claim of 23.8 FPS (Table 1, `sections/4-exp.tex`) is compared against baselines running at 0.13–0.77 FPS. However, the experimental setup does not explicitly state whether these baselines were evaluated on the same H200 GPU with identical batch sizes and resolution settings. Given that inference speed is highly sensitive to hardware and implementation details, a direct comparison without controlled variables undermines the validity of the "30-180x faster" claim. The authors must either re-run all baselines on the same hardware under identical conditions or provide a detailed breakdown of the hardware and configuration differences to justify the speedup ratio.

Second, the core evaluation metrics for garment consistency (HGC, LGC, NTP) rely exclusively on Gemini-3.0 as an automated judge (Appendix, `sections/X-suppl.tex`). While LLM-as-a-judge is becoming common, the paper lacks a validation step correlating these scores with human preferences. The user study (Figure `user_preference.pdf`) is presented separately but does not explicitly validate the correlation with the automated metrics. Without a reported correlation coefficient (e.g., Spearman's rho) between the Gemini scores and human annotations on a held-out set, the quantitative superiority shown in Table 1 is not robustly supported.

Third, the ablation studies (Table 2, `sections/4-exp.tex`) present point estimates for the temperature coefficient $\tau$ without error bars or standard deviations. The difference in Amplitude scores between $\tau=0.2$ (0.8395) and $\tau=0.3$ (0.5106) is substantial, but it is unclear if this is statistically significant or a result of random initialization variance. The authors should report results averaged over multiple random seeds (e.g., 3-5 seeds) with standard deviations to ensure the observed improvements are reproducible and not artifacts of specific runs.

Finally, the training data scale (62K triplets) is mentioned, but the data scale for the competing baselines is not discussed. If baselines like VACE or Kaleido were trained on orders of magnitude more data, the performance gap might be attributed to data scale rather than the proposed method's architectural innovations. A discussion on data scale parity or a controlled experiment is necessary to isolate the contribution of the proposed techniques.
