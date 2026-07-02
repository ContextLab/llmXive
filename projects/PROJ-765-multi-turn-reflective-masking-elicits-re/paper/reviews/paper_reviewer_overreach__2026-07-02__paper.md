---
action_items:
- id: e31fcf06eb55
  severity: science
  text: The claim that RM provides 'native test-time scaling' (Abstract, Intro) is
    overreaching. The paper demonstrates performance gains with fixed T=6 steps (Appendix
    A.3) but does not empirically show that increasing T (scaling compute) yields
    monotonic improvements or converges to a better solution compared to baselines.
    This needs explicit scaling curves to justify the 'scaling' terminology.
- id: d54c4736348c
  severity: writing
  text: The assertion that the method 'elicits reasoning' (Title, Abstract) is too
    strong for the Sudoku and text results. The improvements on MATH500 are marginal
    (+2.4%) and the method relies on oracle-labeled synthetic data (Eq. 3) that explicitly
    teaches the model to correct known errors. This demonstrates learning a correction
    policy, not necessarily emergent reasoning capabilities beyond the training distribution.
- id: d15a29ad2084
  severity: writing
  text: The claim that History Reference is 'parameter-free' (Abstract, Intro) is
    technically true regarding learnable weights but overstates the efficiency. The
    method requires maintaining and updating an accumulated embedding vector $a_i^{(t)}$
    for every position at every step, which increases memory bandwidth and compute
    overhead compared to standard MDM inference. The paper should clarify this trade-off
    rather than implying zero cost.
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:36:10.887698Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the provided empirical evidence, particularly regarding the nature of "reasoning" and "test-time scaling."

First, the central claim that the method "elicits reasoning" (Title, Abstract, Introduction) is an over-interpretation of the results. The training paradigm (Section 3.3, Eq. 3) relies on an oracle revision rule $\tau(z_i, \xstar_i)$ that requires access to the ground-truth target $\xstar_i$ to determine the correct action (mask, reveal, or keep). The model is trained to mimic this oracle on synthetic trajectories. While the method improves performance on benchmarks like MATH500 and MBPP, the gains are modest (e.g., +2.4% on MATH500, Table 2) and the model is essentially learning to correct errors it was explicitly taught to identify during training. This demonstrates the successful transfer of a correction policy, but does not substantiate the claim that the model has acquired a general "reasoning" capability or can self-correct in the absence of such strong supervisory signals during training. The term "reasoning" should be tempered to "iterative refinement" or "error correction" unless the authors can demonstrate emergent reasoning on out-of-distribution tasks without oracle guidance.

Second, the assertion that the approach provides "native test-time scaling" (Abstract, Introduction) is not fully supported. The paper fixes the number of denoising steps to $T=6$ for all experiments (Appendix A.3). To justify the term "scaling," the authors should demonstrate that increasing the number of inference steps (and thus compute) leads to consistent performance improvements, ideally showing a scaling law or convergence behavior that outperforms baselines under increased compute budgets. Without such analysis, the claim remains speculative.

Finally, the description of History Reference as "parameter-free" (Abstract, Introduction) is technically accurate regarding learnable weights but potentially misleading regarding computational cost. The method requires maintaining a running accumulated embedding $a_i^{(t)}$ for every token at every step, involving matrix rotations and additions. This introduces non-trivial memory and compute overhead compared to standard MDM inference. The paper should clarify this trade-off rather than implying the mechanism comes at no cost.
