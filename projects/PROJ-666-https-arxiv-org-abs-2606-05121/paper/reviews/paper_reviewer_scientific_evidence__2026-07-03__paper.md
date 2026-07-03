---
action_items:
- id: a8ee86a58907
  severity: science
  text: The claim that the model 'retains over 91% of its single-segment accuracy'
    as stream length N grows to 5 (Section 5.2, Enh.3) lacks explicit statistical
    evidence. The text references Figure 7 (fig:ablation_stability) for this data,
    but the specific accuracy values, standard deviations, or confidence intervals
    for N=1 through N=5 are not provided in the text or tables. Please report the
    exact accuracy percentages and variance metrics for each N to substantiate the
    91% retention claim.
- id: 20ceb088a051
  severity: science
  text: The ablation study in Table 4 (tab:ablation_data) reports trigger accuracy
    improvements (e.g., V2 to V5) but omits standard deviations or significance tests.
    Given the sparse nature of 'proactive' events, small sample fluctuations could
    drive these gains. Please include standard deviations over multiple seeds or a
    statistical significance test (e.g., paired t-test) to confirm the robustness
    of the TFJP and event selection contributions.
- id: 5ac544c118d5
  severity: science
  text: The real-world validation in Appendix A.1 (Real-World Validation) reports
    a drop in trigger accuracy from 62.0% (synthetic) to 58.9% (natural) but does
    not specify the sample size (number of events or hours) or the confidence interval
    for this 3.1% drop. To support the claim that the model 'retains the bulk' of
    performance, please provide the N value and statistical bounds for the real-world
    evaluation.
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:11:45.074622Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architectural shift toward streaming audio interaction, supported by a large-scale dataset (StreamAudio-2M) and a novel training framework. However, the scientific evidence supporting the robustness of the central claims regarding long-stream stability and the statistical significance of ablation results requires strengthening.

First, the claim in Section 5.2 ([Enh.3]) that the model "retains over 91% of its single-segment accuracy" as the stream extends to 5 segments is critical to the argument of long-stream robustness. While Figure 7 (fig:ablation_stability) is cited, the text does not explicitly state the accuracy values for N=1 through N=5, nor does it provide error bars or standard deviations. Without these specific numbers, the "91%" figure appears to be an approximation that cannot be independently verified. The authors should explicitly list the accuracy percentages for each stream length in the text or a table to validate this specific metric.

Second, the ablation studies in Table 4 (tab:ablation_data) and Table 5 (tab:ablation_lambda) demonstrate clear trends (e.g., the impact of TFJP preprocessing or the dual-loss weight $\lambda$). However, these tables report single-point estimates without measures of variance (standard deviation) or statistical significance testing. In deep learning experiments, especially those involving sparse supervision signals like "proactive" triggers, performance can fluctuate significantly between random seeds. The absence of variance metrics makes it difficult to determine if the observed improvements (e.g., the 3.9% drop in trigger accuracy when removing event selection) are robust or potentially due to random initialization variance. Including results from multiple seeds (e.g., mean $\pm$ std) would significantly strengthen the evidence.

Finally, the real-world validation in Appendix A.1 reports a performance drop on natural audio (58.9% vs. 62.0% on synthetic). While this is a positive finding, the sample size (number of events or total hours) and the confidence intervals for these metrics are not provided. To robustly claim that the model generalizes well, the authors must specify the statistical power of this evaluation.

Overall, the methodology is sound, but the reporting of statistical evidence needs to be more rigorous to fully support the claims of stability and robustness.
