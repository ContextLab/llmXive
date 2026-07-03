---
action_items:
- id: 857c45ea8e7d
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations) for the reported success rates in Tables 1, 2, and 3. The
    current presentation of single-point estimates (e.g., 97.9%, 83.6%) without variance
    metrics makes it impossible to assess the robustness of the gains over baselines
    like pi_0.5 or GR00T.
- id: a1f1f06d8f11
  severity: science
  text: Clarify the sample size (N) and number of random seeds used for the real-world
    ALOHA experiments (Table 2). The text mentions 'real-world ALOHA experiments'
    but does not specify if the reported 83.6% average is an aggregate of multiple
    trials, seeds, or a single run, which is critical for evaluating the reliability
    of the OOD claims.
- id: 03f4827bba96
  severity: science
  text: Provide a detailed description of the randomization strategy and sample size
    for the DOMINO dynamic manipulation benchmark (Table 4). The claim of 26.6% zero-shot
    success is significant; the review requires evidence that this result is not an
    artifact of a specific seed or a small, non-representative subset of the 35 suites
    mentioned.
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:13:22.444384Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a unified Vision-Language-Action (VLA) model with ambitious claims regarding generalization across tasks, environments, and embodiments. While the scale of the pretraining data and the architectural design (DiT-based flow matching) are impressive, the scientific evidence supporting the central claims of robustness and superiority lacks necessary statistical rigor.

The primary concern is the absence of variance metrics. Tables 1, 2, and 3 report single-point success rates (e.g., 97.9% on LIBERO, 83.6% on ALOHA) without standard deviations, confidence intervals, or p-values. In robotics and embodied AI, performance can vary significantly based on random seeds, initial object poses, and environmental noise. Without reporting the standard deviation over multiple seeds (typically N=5 or N=10) or trials, it is impossible to determine if the reported improvements over baselines (e.g., the +35.4pp gain over $\pi_{0.5}$ in OOD tasks) are statistically significant or potentially due to favorable random initialization.

Furthermore, the real-world evaluation on ALOHA (Table 2) lacks transparency regarding the experimental protocol. The manuscript states the model was evaluated on "short-horizon and long-horizon task categories" but does not specify the number of trials per task, the number of seeds, or the specific randomization of object placements used during evaluation. Given the high success rates reported (e.g., 98.7% for Bowl Stacking), the lack of error bars raises concerns about the robustness of these results to minor perturbations.

Finally, the Out-of-Distribution (OOD) claims on the DOMINO benchmark (Table 4) rely on a zero-shot setting. While the result of 26.6% is notable, the paper does not detail the distribution of the 35 suites or the number of episodes per suite used to calculate this average. If the evaluation was conducted on a small number of episodes per suite, the result could be highly volatile. The authors must provide the sample size (N) and variance for all key quantitative results to substantiate the claim of "robust multi-task performance and OOD generalization."
