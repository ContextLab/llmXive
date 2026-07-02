---
action_items:
- id: 6ac77575049c
  severity: science
  text: Table 1 (Video-MME-v2) reports a 13.9 point gap between Keye-VL-2.0 (42.4)
    and Qwen3.5 (28.5) on 512-frame inputs, yet the text claims 'state-of-the-art'
    without reporting standard deviation or confidence intervals. Provide statistical
    significance testing (e.g., t-tests) or error bars to confirm this gain is not
    due to random variance.
- id: 2e90c86dbf7a
  severity: science
  text: The claim of 'lossless 256K context' (Abstract, Section 1) lacks empirical
    validation. The paper reports performance on 512-frame benchmarks but does not
    provide a controlled ablation study comparing 256K context performance against
    a dense-attention baseline or a subsampled baseline to prove the 'lossless' nature
    of the sparse aggregation.
- id: d1cdf10dbc2b
  severity: science
  text: The Video-RL section (Section 3.2.4) cites a '1% improvement' from 31K video
    samples but does not specify the baseline metric or the specific benchmark subset.
    Without the baseline score and the specific evaluation protocol, this effect size
    is unverifiable and risks p-hacking interpretation.
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:26:19.426551Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a technically ambitious architecture (MoE + DSA) for long-context multimodal modeling, but the scientific evidence supporting the central claims of "lossless" scaling and "state-of-the-art" performance is currently insufficient due to a lack of statistical rigor and controlled ablation studies.

First, the performance claims in Table 1 (Section 4.1) rely on point estimates without measures of uncertainty. For instance, the reported 13.9% absolute gain on Video-MME-v2 (512 frames) over Qwen3.5 is substantial, but without standard deviations, confidence intervals, or significance testing (e.g., paired t-tests across multiple seeds), it is impossible to rule out random variance or benchmark-specific noise. In high-stakes model comparisons, reporting only mean scores is a methodological weakness that undermines the robustness of the "SOTA" claim.

Second, the core architectural claim of "lossless 256K context" (Abstract, Section 1) is not empirically substantiated. The paper demonstrates performance on benchmarks with up to 512 frames but does not provide a direct comparison against a dense-attention baseline at equivalent context lengths, nor does it show a degradation curve as context length increases. To validate the "lossless" assertion, the authors must demonstrate that the sparse attention mechanism (DSA) retains information critical for reasoning at 256K tokens that would be lost in standard subsampling or truncation strategies. The current evidence is correlational (high scores on long-video benchmarks) rather than causal (proving the mechanism preserves information).

Finally, the reported "1% improvement" from Video-RL (Section 3.2.4) is presented without a clear baseline or statistical context. A 1% gain on a specific subset of 31K samples could be a statistical fluke or a result of overfitting to the specific reward model (Qwen2.5-VL-72B) used for evaluation. The authors should clarify the baseline metric, the specific benchmark subset used for this claim, and whether the improvement holds across different evaluation seeds.

To strengthen the scientific validity of the report, the authors must include error bars or significance tests for all major benchmark comparisons, provide an ablation study isolating the effect of the DSA module on long-context retention, and fully detail the experimental setup for the RL improvements.
