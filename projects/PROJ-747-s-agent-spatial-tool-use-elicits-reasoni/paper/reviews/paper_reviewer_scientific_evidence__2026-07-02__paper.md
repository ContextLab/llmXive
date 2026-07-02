---
action_items:
- id: 329d9898e8fc
  severity: science
  text: The ablation study in Table 2 (tab:ablation_config) lacks statistical significance
    testing. With only a single run reported for each configuration (e.g., 56.7% vs
    58.2%), it is unclear if the gains from memory modules are robust or due to random
    variance. Please report standard deviations over multiple seeds or perform a significance
    test.
- id: 68fe5a3a9976
  severity: science
  text: The claim that S-Agent-8B 'performs comparably' to GPT-5.4 and Gemini 3 Pro
    (Abstract, Intro) is not fully supported by the data in Table 1 (tab:trajectory_distillation).
    On ReVSI, S-Agent-8B scores 52.8% while Gemini 3 Pro scores 60.9%, a gap of 8.1
    points. The authors should qualify this claim or provide a more nuanced comparison
    rather than asserting comparability across all metrics.
- id: 53f8c7dafb0d
  severity: science
  text: The training data construction (S-300K) relies on a 'frozen teacher' (GPT-5.4)
    to generate trajectories, which are then filtered for correctness. This introduces
    a potential bias where the student model learns to mimic the specific reasoning
    patterns and tool preferences of the GPT-5.4 teacher, potentially limiting generalization
    to other planners or scenarios where the teacher fails. The authors should discuss
    this teacher-student bias and its impact on the robustness of the distilled agent.
artifact_hash: daf6f96ab0f7dc8b7f7a6cf5f7a9c2a699ed007819d222e3f1594a2f92961a95
artifact_path: projects/PROJ-747-s-agent-spatial-tool-use-elicits-reasoni/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:58:41.668438Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented for S-Agent is generally strong, demonstrating consistent improvements over baselines across multiple benchmarks (MMSI-Bench, ViewSpatial-Bench, ReVSI). The ablation studies in Section 4.4 (Table 2) effectively isolate the contributions of the hierarchical evidence levels and memory modules, showing that Level-3 experts and memory are critical for performance. The qualitative analysis in Section 4.5 provides concrete examples of how the agent corrects errors through tool use, supporting the central claim of evidence accumulation.

However, there are three specific concerns regarding the robustness and interpretation of the evidence:

1.  **Statistical Robustness of Ablations:** The ablation study (Table 2, `tab:ablation_config`) reports single-point accuracy scores for each configuration (e.g., 56.7% for "Spatial only" vs. 58.2% for "+ Scene memory"). Given the small magnitude of some gains (e.g., 1.5% from scene memory), it is essential to know if these improvements are statistically significant. The paper does not report standard deviations from multiple random seeds or any significance testing (e.g., t-tests). Without this, it is difficult to rule out that the observed gains are due to random variance in the evaluation or the specific initialization of the planner.

2.  **Overstated Comparability to Closed-Source Models:** The abstract and introduction claim that S-Agent-8B "performs comparably" to advanced closed-source models like GPT-5.4 and Gemini 3 Pro. While S-Agent-8B outperforms the base Qwen3-VL-8B significantly, the data in Table 1 (`tab:trajectory_distillation`) shows a notable gap on the ReVSI benchmark (52.8% for S-Agent-8B vs. 60.9% for Gemini 3 Pro). On MMSI-Bench, the gap is smaller (41.6% vs. 45.2%), but the claim of "comparability" across the board is an overstatement given the 8-point deficit on ReVSI. The authors should refine this claim to reflect the specific areas of parity and the areas where a gap remains.

3.  **Teacher-Student Bias in Distillation:** The S-300K dataset is constructed by generating trajectories with a GPT-5.4 teacher and filtering for correctness. This methodology risks the student model (S-Agent-8B) overfitting to the specific reasoning heuristics, tool selection strategies, and potential biases of the GPT-5.4 teacher. If the teacher fails on a specific type of spatial query or uses a suboptimal tool sequence that happens to yield the correct answer, the student may learn this suboptimal behavior. The paper does not discuss the potential for this "teacher bias" to limit the generalization of the distilled agent to scenarios where the teacher's strategy is not optimal or where a different planner might be used. A discussion on the robustness of the distilled policy to variations in the teacher or the inclusion of diverse reasoning paths would strengthen the evidence.
