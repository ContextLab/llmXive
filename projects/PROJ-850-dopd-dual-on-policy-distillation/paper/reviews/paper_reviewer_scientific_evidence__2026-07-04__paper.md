---
action_items:
- id: da4d2ba49ec5
  severity: writing
  text: The paper presents a compelling hypothesis regarding "privilege illusion"
    in on-policy distillation and proposes DOPD to mitigate it. However, the evidentiary
    strength of the central claims is currently undermined by a lack of statistical
    rigor in the experimental design. The primary concern is the absence of variance
    reporting. Tables 1 and 2 present headline accuracy numbers (e.g., 71.3 vs 68.3)
    derived from what appears to be single runs. In the context of LLM/VLM training,
    performance can fl
artifact_hash: 1c1c61b84dddc2460538527d82a1400d1a11188ffd68bb62d1afc40f8faa40cf
artifact_path: projects/PROJ-850-dopd-dual-on-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:22:42.390387Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis regarding "privilege illusion" in on-policy distillation and proposes DOPD to mitigate it. However, the evidentiary strength of the central claims is currently undermined by a lack of statistical rigor in the experimental design.

The primary concern is the absence of variance reporting. Tables 1 and 2 present headline accuracy numbers (e.g., 71.3 vs 68.3) derived from what appears to be single runs. In the context of LLM/VLM training, performance can fluctuate significantly based on random seed initialization, data shuffling, and rollout sampling. Without reporting results across multiple seeds (e.g., 3-5) with standard deviations or confidence intervals, the reader cannot distinguish a genuine methodological improvement from statistical noise or a lucky initialization. A 4-5 point gap, while seemingly large, could easily fall within the variance of a single run for these model sizes.

Furthermore, the comparison against strong baselines (ExOPD, Uni-OPD) lacks transparency regarding experimental fairness. The paper states baselines were "rerun," but does not specify if they received the same hyperparameter search effort or privileged information generation quality as DOPD. If the baselines were under-tuned relative to the proposed method, the reported superiority of DOPD may be an artifact of tuning asymmetry rather than the core algorithm.

Finally, the ablation studies (Table 4) conflate the effect of the privileged input with the adaptive routing mechanism. To rigorously claim that the "advantage-aware" routing is the key innovation, the authors must demonstrate that using privileged inputs with a *uniform* (non-adaptive) distillation strategy yields lower performance than the adaptive version. Currently, the design does not fully isolate the specific contribution of the routing logic from the mere presence of the privileged signals.

Addressing these issues requires re-running experiments with multiple seeds and ensuring fair baseline comparisons, which are essential to substantiate the claim that DOPD is a robust and superior paradigm.
