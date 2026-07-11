---
action_items:
- id: 09067f6cdbcb
  severity: writing
  text: The paper presents a compelling diagnostic framework, Video-Oasis, to audit
    video benchmarks. However, the evidentiary strength of the core quantitative claims
    is weakened by a lack of reported variance and insufficient controls in the ablation
    studies. First, the headline finding that "55% of existing benchmark samples are
    solvable without visual input" (Abstract) and the detailed breakdowns in Table
    2 and Table 3 are presented as aggregate point estimates. The paper does not report
    standard de
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:06:51.703607Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling diagnostic framework, Video-Oasis, to audit video benchmarks. However, the evidentiary strength of the core quantitative claims is weakened by a lack of reported variance and insufficient controls in the ablation studies.

First, the headline finding that "55% of existing benchmark samples are solvable without visual input" (Abstract) and the detailed breakdowns in Table 2 and Table 3 are presented as aggregate point estimates. The paper does not report standard deviations, confidence intervals, or the number of random seeds used for the diagnostic models (Eagle2.5, Qwen2.5-VL, etc.). In large-scale benchmark evaluations, model performance can vary significantly across seeds or minor hyperparameter shifts. Without reporting variance (e.g., mean ± SD over 3-5 seeds), the reader cannot determine if the reported shortcut ratios are stable phenomena or artifacts of a specific model initialization. The claim that "state-of-the-art models perform only marginally above random guessing" on the distilled set (Table 7) similarly lacks variance metrics, making it difficult to assess the statistical significance of the gap between models.

Second, the ablation study on temporal grounding in Section 5.1 (Table 8) introduces a potential confound. The authors report modest accuracy gains (1.4% to 2.3%) when adding the AKS temporal grounding module. However, the AKS module involves an additional retrieval step that likely increases inference time and computational cost compared to the baseline. The design does not control for this "compute budget" difference. It is plausible that the performance gain arises simply from the model having access to more processed information or a longer inference window, rather than the specific logic of the AKS grounding. To isolate the contribution of the grounding mechanism, the authors should run a control experiment where the baseline model is given an equivalent amount of compute or retrieved frames (e.g., via a random or naive retrieval strategy) to ensure the gain is not merely a function of increased resources.

Finally, the categorization of video-native challenges (Section 4.1) relies on an ensemble of proprietary LLMs (GPT-4o, GPT-5, etc.) to label the filtered samples. While the authors mention a consensus threshold, they do not report the inter-annotator agreement (e.g., Cohen's Kappa) or the variance in category distribution if different model ensembles were used. Given that the subsequent evaluation (Table 7) is broken down by these categories, the stability of these labels is critical. If the categorization is noisy, the observed performance differences across categories (e.g., "Global Narrative" being the hardest) could be an artifact of label inconsistency rather than a true capability gap.

Addressing these issues by reporting variance metrics for the diagnostic results and adding a compute-matched control for the grounding ablation would significantly strengthen the scientific validity of the paper's conclusions.
