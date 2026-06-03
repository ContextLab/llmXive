---
action_items:
- id: 79f91be6d00e
  severity: science
  text: Report number of trials, seeds, and variance (std dev/confidence intervals)
    for all success rate metrics in Tables 1-5.
- id: c66a5f856105
  severity: science
  text: Clarify the exact evaluation protocol for real-world ALOHA tasks (e.g., N
    trials per task, randomization details).
- id: 4b613c84b756
  severity: science
  text: Justify the comparison between zero-shot Qwen-VLA and fine-tuned baselines
    in DOMINO (Table 5) regarding task sampling and seeds.
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T04:47:24.680129Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented to support Qwen-VLA's generalization claims requires greater statistical rigor. While the ablation studies (Section 5.2) and benchmark comparisons (Tables 1-5) are extensive, critical reporting details regarding experimental reproducibility are missing.

First, success rates in Tables 1-5 are reported as single percentages without standard deviations, confidence intervals, or the number of evaluation seeds. For instance, Table 2 reports real-world ALOHA performance as "96.2%" and "92.3%". These precise decimals imply a specific trial count (e.g., 100 trials), yet the number of trials ($N$) is not stated. Without knowing $N$ and the variance, it is impossible to assess the statistical significance of the reported gains (e.g., the 40.7% OOD improvement in Table 3). Standard practice in embodied AI requires reporting mean $\pm$ std dev over at least 3-5 random seeds or a minimum of 25-50 trials per task.

Second, the real-world evaluation protocol (Section 5.1.2) lacks detail. It is unclear if the "success" metric is binary or continuous, and whether the evaluation was automated or human-scored. For the DOMINO benchmark (Table 5), Qwen-VLA-Instruct claims to outperform fine-tuned baselines (e.g., PUMA) in a zero-shot setting. This is a strong claim that requires ensuring the task distribution and random seeds for the zero-shot evaluation match those used for the fine-tuned baselines to rule out variance in task sampling.

Finally, the ablation on embodiment-aware prompting (Section 5.2.1) focuses on projection designs and VL data, but does not explicitly ablate the prompt conditioning itself. A control using a generic prompt (without embodiment details) is necessary to quantify the specific contribution of the prompt to cross-embodiment transfer. Additionally, the synthetic data volume (7.2M trajectories in Section 3.1.2) is substantial, but the diversity of procedural generation needs validation against real-world distribution shifts to ensure the OOD claims are not artifacts of the simulator's randomization. Addressing these points will significantly strengthen the empirical validity of the central claims regarding robustness and generalization.
