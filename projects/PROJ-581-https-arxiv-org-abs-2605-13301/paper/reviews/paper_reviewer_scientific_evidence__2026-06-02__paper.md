---
action_items:
- id: d5fe6eaffeb4
  severity: science
  text: Report confidence intervals or standard deviations for all benchmark percentages
    in Table 1 to account for small sample sizes (e.g., AIME problems).
- id: de4fb95a989e
  severity: science
  text: Clarify TTS usage and inference compute budgets for baseline models (Gemini
    3.1 Pro, GPT-5.5) to ensure fair comparison against SU-01's TTS results.
- id: 0c34a4240dc7
  severity: science
  text: Report inter-annotator agreement (e.g., Cohen's kappa) for the human expert
    scoring on IMO 2025 and USAMO 2026 to validate score stability.
- id: 609b4fce7a98
  severity: science
  text: Provide performance variance across multiple random seeds for the RL training
    stage (200 steps) to demonstrate convergence stability and generalization.
artifact_hash: 6b23039f76721ac00eaa6c408647f026893a62ad0f423ddd12fdde82e2327635
artifact_path: projects/PROJ-581-https-arxiv-org-abs-2605-13301/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T13:52:04.444934Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling ablation evidence for the proposed pipeline (SFT → RL → TTS), particularly in Figure 5 and Table 1, demonstrating consistent gains across stages. However, the statistical robustness of the central claims requires strengthening. Table 1 reports benchmark percentages (e.g., 77.5% on AnswerBench) without confidence intervals or standard deviations. Given the small sample sizes inherent in benchmarks like AIME (typically ~30 problems) and the Olympiad competitions (6 problems each), single-point estimates are insufficient to rule out variance or chance.

Furthermore, the comparison against baselines in Table 2 and Table 3 lacks clarity on inference compute budgets. While SU-01 explicitly uses Test-Time Scaling (TTS), baselines like "Gemini 3.1 Pro Thinking" and "GPT-5.5-High" may inherently employ similar scaling mechanisms not accounted for in the comparison. Section 6.2 details SU-01's TTS budget (MAX_RUNS=10), but does not normalize performance against inference tokens for the baselines, potentially conflating scaling effects with model capability.

Additionally, the RL training claims 200 steps (Section 4.2, Appendix RL Training Details). While efficient, convergence stability across random seeds is not reported. A single run could overfit to the specific 8,967 verifiable prompts. Variance across seeds would strengthen the claim that the "simple" recipe generalizes.

Finally, the human evaluation protocol for IMO 2025 and USAMO 2026 (Appendix Evaluation Details) relies on three gold-medal experts reporting the "worst score." While conservative, this masks inter-annotator disagreement. Reporting Cohen’s kappa or standard deviation across evaluators is necessary to validate the stability of the 35-point scores. Without variance metrics on the competition results and baseline inference budgets, the claim of "Gold-Medal-Level" superiority remains statistically fragile.
