---
action_items:
- id: f4531b507398
  severity: writing
  text: Temper the claim of 'internalized spatial reasoning' in captions (e.g., Fig.
    pt_viz) given the admitted 'spatial imprecision' and 'visually degraded' outputs
    (Fig. qwen_ipt_qual).
- id: a6535a0e1003
  severity: science
  text: Clarify the training/test split for AI2-THOR in Table pt_breakdown to rule
    out data leakage between ProcTHOR training and iTHOR testing.
- id: 98b90d558284
  severity: science
  text: Include Multiview Counting results in the main results table to support the
    broader 'Spatial Reasoning' title claim, as currently only Path Tracing is detailed.
- id: 78152e8bc822
  severity: writing
  text: Discuss limitations regarding the dominance of synthetic data (AI2-THOR/Habitat)
    in the training set versus the real-world benchmark size (332 questions).
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:14:38.150756Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a strong claim that Imaginative Perception Tokens (IPT) enhance spatial reasoning, but several extrapolations exceed the provided evidence.

First, the title and abstract generalize to "Spatial Reasoning," yet the detailed results in Table~\ref{tab:pt_breakdown} focus almost exclusively on Path Tracing. Multiview Counting statistics are provided in Table~\ref{tab:dataset_stats}, but performance metrics are absent from the main results section. Without quantitative evidence on counting or other spatial tasks, the broad claim of enhanced spatial reasoning is overreaching.

Second, the mechanism of "internalized spatial reasoning" is inferred from visualizations (Fig.~\ref{fig:pt_viz}) where the authors explicitly admit the generated thoughts exhibit "spatial imprecision and artifacts." Concluding that this proves internalized reasoning rather than pattern matching or feature alignment is speculative. The caption states the model "arrives at the correct answer" despite imprecision, but this does not rule out shortcut learning. This causal link requires more rigorous ablation or probing.

Third, there is a potential data leakage concern in the Path Tracing results. The training set includes ProcTHOR-10k and AI2-THOR scenes (Supp. Data Curation), while Table~\ref{tab:pt_breakdown} reports results on "AI2-THOR" splits (EgoDir, Path, PathArr). If the test scenes overlap with the training distribution (e.g., same house layouts), the reported gains (e.g., Bagel 73.5% vs GPT-5 61.1%) may reflect overfitting rather than generalizable reasoning. The distinction between training (ProcTHOR) and testing (iTHOR) scenes must be explicitly clarified to validate the generalization claim.

Finally, the transition from discrete tokens (Qwen2.5-VL) to continuous latents (BAGEL) is motivated by the "visually degraded" outputs of the former (Fig.~\ref{fig:qwen_ipt_qual}). However, the discrete PET results show negligible improvement (50.0% vs 50.0% for 3B). The paper should acknowledge that IPT benefits may be model-architecture dependent rather than a universal property of the token type.

Please address these points to align the claims with the empirical evidence.
