---
action_items:
- id: d045dd31acd6
  severity: writing
  text: The paper presents a compelling architecture and training pipeline, but the
    evidentiary support for its central claims regarding performance superiority and
    physical grounding relies heavily on internal benchmarks and qualitative results
    that lack necessary statistical rigor. First, the primary quantitative evidence
    in Section 6.1 (Internal Benchmark) and Table 1 (RBench) is presented as single-point
    estimates. For the internal benchmark, the paper does not disclose the number
    of prompts used, t
artifact_hash: 9ee70f69980a19ab6b09b1ef85c408bba9d6c20db5c959c0faf89cac5e30112c
artifact_path: projects/PROJ-1026-scaling-mixture-of-experts-video-pretrai/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:02:37.751486Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architecture and training pipeline, but the evidentiary support for its central claims regarding performance superiority and physical grounding relies heavily on internal benchmarks and qualitative results that lack necessary statistical rigor.

First, the primary quantitative evidence in Section 6.1 (Internal Benchmark) and Table 1 (RBench) is presented as single-point estimates. For the internal benchmark, the paper does not disclose the number of prompts used, the number of generation seeds per prompt, or the variance (standard deviation) across seeds. In generative modeling, performance can fluctuate significantly based on random initialization and prompt selection. Without reporting mean ± standard deviation over multiple seeds (e.g., 3-5) and a clear description of the prompt distribution, the reported "state-of-the-art" margins could easily be artifacts of a lucky seed or a favorable subset of prompts. The same concern applies to the RBench and Physics-IQ results; while these are public benchmarks, the paper does not explicitly confirm that all baselines were evaluated with identical inference hyperparameters (e.g., CFG scale, sampling steps, resolution). If the proposed model benefited from extensive hyperparameter tuning while baselines were run with defaults, the observed gains would reflect tuning effort rather than the intrinsic superiority of the MoE architecture.

Second, the claim that post-training with Reinforcement Learning (RL) significantly enhances physical plausibility (Section 5.2) is supported almost exclusively by qualitative figures (Figures 5 and 6) and a user study. While the user study provides some quantitative backing, it is limited to pairwise comparisons on a specific set of prompts and does not isolate the specific contribution of the RL objective against a non-RL baseline on a standardized metric. The absence of automated, quantitative metrics (e.g., success rates on a held-out physical reasoning test set or automated physics violation scores) for the RL vs. pre-trained comparison makes it difficult to rule out that the observed improvements are due to random variation or the specific selection of examples shown. To substantiate the claim that the RL phase is necessary for physical grounding, the authors should provide a quantitative evaluation on a held-out test set with multiple seeds, demonstrating a statistically significant improvement over the pre-trained model.

Finally, the scaling experiments in Section 2.3 (Scaling Experiments) rely on training and validation loss curves to argue for scalability. While these curves show consistent trends, they do not directly measure the downstream task performance (e.g., video generation quality or physical reasoning) at different scales. The claim that the model scales predictably to 120B parameters is based on early-stage training trajectories that are "not trained to full convergence." Without reporting downstream metrics for the larger models, the evidence for their practical utility remains indirect.

To strengthen the paper, the authors should: (1) report variance (mean ± SD) for all benchmark results across multiple seeds; (2) explicitly state and control for inference hyperparameters in all baseline comparisons; and (3) provide quantitative, automated metrics for the RL post-training improvements on a held-out test set.
