---
action_items:
- id: b462b134085a
  severity: science
  text: "The manuscript presents an informal argument that the power\u2011then\u2011\
    retract update drives router rows toward the principal singular direction (Section\u202F\
    3.2). However, no rigorous convergence proof or quantitative analysis of the rate\
    \ of alignment is provided. Add a formal theorem (or clearly state the assumptions)\
    \ and empirical metrics (e.g., alignment error over training steps) to substantiate\
    \ this claim."
- id: ebff08ff754e
  severity: writing
  text: "Claims that MPI \u201Cconsistently facilitates faster convergence, superior\
    \ downstream performance, and improved load balancing\u201D are based on a limited\
    \ set of experiments (up to 11\u202FB parameters, specific token counts, and a\
    \ single downstream benchmark suite). The paper should temper these statements\
    \ or broaden the evaluation to include more model sizes, datasets, and alternative\
    \ baselines."
- id: a7fdce13db9b
  severity: writing
  text: "The statement that the method incurs \u201Czero inference overhead\u201D\
    \ overlooks the need to run a power\u2011iteration pass on the router weights\
    \ at model load time, which can be non\u2011trivial for very large expert counts.\
    \ Clarify the actual cost and any potential latency impact."
- id: 07b658293a28
  severity: science
  text: "Section\u202F5.2 claims compatibility with other router designs (e.g., auxiliary\
    \ losses, sigmoid activation) based on a handful of small\u2011scale experiments.\
    \ Provide systematic ablations across multiple activation functions, loss terms,\
    \ and optimizer settings, or qualify the claim as preliminary."
- id: 43c8232acc2d
  severity: writing
  text: "The paper repeatedly describes MPI as a \u201Cprincipled\u201D and \u201C\
    fundamental\u201D redesign, yet the empirical gains are modest (\u22480.01\u2013\
    0.02\u202F% loss reduction, a few percentage points on downstream tasks). Discuss\
    \ the practical significance of these improvements and potential trade\u2011offs\
    \ (e.g., added complexity, stability issues noted in the ablations)."
- id: 666c7ff6babe
  severity: science
  text: "The theoretical section (Eq.\u202F10) derives an approximation for the update\
    \ but does not quantify the approximation error or its impact on training stability.\
    \ Include an error analysis or empirical verification of the approximation\u2019\
    s validity."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:38:57.850897Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper introduces Manifold Power‑Iteration (MPI) as a redesign of Mixture‑of‑Experts (MoE) routers, arguing that aligning each router row with the principal singular direction of its associated expert yields better routing and faster convergence. While the intuition is appealing, several claims extend beyond what the presented evidence supports.

1. **Theoretical Overreach (Section 3.2)** – The authors claim that a single power‑iteration step “drives router rows to converge toward the principal singular directions” and that the update is equivalent to a steepest‑ascent step on a spherical manifold. The manuscript provides only a heuristic derivation and an approximation (Eq. 10) without a formal convergence theorem, error bounds, or assumptions about the expert weight spectra. This leaves the central theoretical claim under‑justified.

2. **Empirical Scope (Sections 4–5)** – All experiments are confined to 1 B, 3 B, and 11 B parameter models trained on a single pretraining corpus (FineWeb‑Edu) and evaluated on a fixed set of 25 downstream tasks. The reported improvements (≈0.01–0.02 % loss reduction, 1–3 % absolute accuracy gains) are modest and may not generalize to other data regimes, larger scales, or different MoE configurations. The claim that the superiority is “robust to shifts in model features” is therefore overstated.

3. **Compatibility Claims (Section 6)** – Compatibility with auxiliary losses, alternative activations, and other router designs is demonstrated only on small‑scale 1 B models with limited hyperparameter sweeps. Generalizing this to all MoE variants is premature without broader ablations.

4. **Inference Overhead** – The statement that MPI incurs “zero inference overhead” neglects the need to apply power‑iteration to router weights at model load time. For models with hundreds of experts, this preprocessing step can be non‑trivial and should be quantified.

5. **Stability Issues** – Ablation studies (Figure 4) show that removing the retraction step leads to loss spikes and training collapse for certain optimizers. This indicates that MPI introduces stability concerns that are not fully addressed in the main narrative.

6. **Impact vs. Complexity** – The paper positions MPI as a “fundamental departure” and “intrinsic improvement” to MoE routing, yet the empirical gains are relatively small compared to the added algorithmic complexity (power iteration, norm retraction, hyperparameter C). A more balanced discussion of trade‑offs is needed.

In summary, the manuscript presents an interesting idea but currently overstates its theoretical guarantees and empirical generality. Strengthening the theoretical analysis, expanding the experimental evaluation, and providing a more nuanced discussion of practical implications are necessary before acceptance.
