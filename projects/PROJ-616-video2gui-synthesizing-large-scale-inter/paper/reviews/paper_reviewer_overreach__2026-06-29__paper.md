---
action_items:
- id: eeae971903a0
  severity: science
  text: The claim of extracting 12.7M trajectories from 500M metadata entries lacks
    caveats on filtering ratios and trajectory definitions. The paper implies high-yield
    conversion without clarifying massive attrition or potential duplicate/fragmented
    trajectories, overstating pipeline efficiency.
- id: b52beb44bbd8
  severity: science
  text: The assertion of spanning 'over 1,500 applications' (Table 1) is an over-claim
    without distribution analysis or unique identification methodology. The paper
    fails to demonstrate how this number was derived or verified, risking inflated
    diversity metrics.
- id: 8cdc615d4ee7
  severity: writing
  text: Claims of 'substantial improvements' on online benchmarks (Figure 2) overreach
    statistical power. Gains like 10.4% to 12.3% on OSWorld are modest, and the 'doubling'
    on AndroidWorld lacks confidence intervals or multiple runs to rule out variance.
- id: 4c3769d378d5
  severity: science
  text: The human evaluation claims 'superior quality' based on only 300 samples rated
    by 5 experts. This sample size is insufficient to support definitive conclusions
    over baselines, especially given high variance in subjective GUI annotation tasks.
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:18:06.440695Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its quantitative claims and the interpretation of its experimental results.

First, the scale of the dataset is presented with an air of absolute precision that the methodology does not fully support. The abstract and introduction claim the extraction of "12.7 million interaction trajectories" from "500 million video metadata entries." While the pipeline is described, the paper fails to explicitly address the massive attrition rate or the potential for fragmentation (e.g., one video yielding multiple disjointed trajectories). Without a clear definition of what constitutes a unique "trajectory" versus a "segment" and a breakdown of the filtering funnel, the claim of 12.7M high-quality, usable trajectories risks overstating the effective data volume. Similarly, the claim of covering "over 1,500 applications and websites" (Table 1) is unsupported by a distribution analysis or a unique identifier methodology. It is unclear if this count includes minor variations of the same app or distinct software, potentially inflating the diversity metric.

Second, the performance claims in the "Main Results" section overstate the significance of the gains. The abstract states the models "match or surpass state-of-the-art performance." While the numbers in Table 2 are competitive, the text glosses over the fact that the proposed 7B models do not universally outperform larger proprietary models (e.g., UI-TARS-72B) or the largest open-source models (Qwen3-VL-32B) across all metrics. The claim of "substantial improvements" on online benchmarks (Figure 2) is particularly fragile; a jump from 10.4% to 12.3% on OSWorld, while positive, is not "substantial" in the context of the field's high difficulty, and the "doubling" claim on AndroidWorld (16.4% to 31.9%) lacks statistical validation (e.g., confidence intervals or multiple runs) to rule out variance.

Finally, the human evaluation section (Data Quality Check) overreaches on the strength of its evidence. Claiming a Krippendorff's alpha of 0.84 and a definitive "superior quality" based on only 300 samples rated by five experts is statistically weak for a dataset of this claimed scale. The small sample size cannot robustly support the broad conclusion that the dataset is superior to baselines across all dimensions of diversity and accuracy. The paper must temper these claims, provide the missing statistical rigor, and clarify the definitions of its scale metrics.
