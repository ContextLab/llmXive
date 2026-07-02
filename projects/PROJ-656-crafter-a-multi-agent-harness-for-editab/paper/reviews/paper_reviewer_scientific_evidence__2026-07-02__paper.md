---
action_items:
- id: d699c6462f39
  severity: science
  text: The human evaluation study (Appendix, Section 'Human Evaluation') reports
    a Cohen's kappa of 0.58 on only 60 samples. This sample size is statistically
    underpowered to validate the VLM judge as a reliable proxy for the full 279-sample
    benchmark. The authors must either expand the human study to a statistically significant
    size (e.g., >200 samples) or provide a power analysis justifying the current N.
- id: 595ffc845abb
  severity: science
  text: Table 1 reports a 0.00% win-rate for open-source baselines (GLM-Image, Qwen-Image)
    on the 279-sample CrafterBench. This absolute failure across all dimensions suggests
    a potential evaluation protocol mismatch (e.g., the VLM judge failing to parse
    open-source outputs) rather than a genuine performance gap. The authors must provide
    qualitative examples or error logs explaining why these models scored zero to
    rule out a systematic evaluation artifact.
- id: 7c47ae58a8cf
  severity: science
  text: The ablation study (Table 2) removes mechanisms one at a time but does not
    report variance (standard deviation) or statistical significance tests (e.g.,
    paired t-tests) for the performance drops. Given the small benchmark size (n=279)
    and the stochastic nature of LLM-based generation, the authors must demonstrate
    that the observed drops (e.g., 5.04 to 8.90 points) are statistically significant
    and not due to random seed variance.
artifact_hash: 561d0fd1ec8bdb715ca61e054c458765d4b88bb2a7f88304cff468b996504a7f
artifact_path: projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:58:32.698737Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel "harness" architecture for scientific figure generation, supported by a new benchmark (CrafterBench) and extensive experiments. However, the scientific evidence supporting the robustness of the claims requires strengthening in three specific areas regarding statistical rigor and evaluation validity.

First, the validation of the automated VLM judge relies on a human evaluation study described in the Appendix (Section "Human Evaluation"). The study reports a Cohen's kappa of 0.58 based on only 60 pairwise comparisons. For a benchmark of 279 samples spanning diverse tasks and figure types, a sample size of 60 is statistically underpowered to establish the judge's reliability as a proxy for human preference. The confidence intervals around this agreement metric are likely wide, and the result may not generalize to the full dataset. The authors should either expand the human study to a statistically robust size (e.g., >200 samples) or provide a formal power analysis justifying why 60 samples are sufficient to validate the metric for the entire benchmark.

Second, the results in Table 1 show that open-source baselines (GLM-Image, Qwen-Image) achieved a 0.00% win-rate across all dimensions on CrafterBench. While these models may be weaker, an absolute zero score across 279 samples and multiple dimensions is highly suspicious and suggests a potential systematic failure in the evaluation protocol (e.g., the VLM judge failing to parse or score the specific output format of these models) rather than a genuine lack of capability. Without qualitative examples or error logs explaining this total failure, the claim that the harness "substantially outperforms" these baselines is difficult to verify. The authors must clarify whether this is a true performance gap or an artifact of the evaluation setup.

Third, the ablation study (Table 2) demonstrates performance drops when removing specific components (ranging from 5.04 to 8.90 points). However, the paper does not report variance (standard deviation) or statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals) for these differences. Given the stochastic nature of LLM-based generation and the relatively small benchmark size, it is unclear if these drops are statistically significant or simply due to random seed variance. The authors should run multiple seeds for the ablation conditions and report statistical significance to confirm that each mechanism's contribution is robust.

Addressing these points will significantly strengthen the scientific validity of the paper's central claims regarding the harness's effectiveness and the reliability of the proposed evaluation metrics.
