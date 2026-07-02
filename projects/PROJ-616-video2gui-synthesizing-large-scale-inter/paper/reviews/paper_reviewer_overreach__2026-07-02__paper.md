---
action_items:
- id: 1997aaa44553
  severity: writing
  text: The claim that the dataset spans 'over 1,500 applications and websites' (Abstract,
    Table 1) lacks a specific methodology for counting unique entities. Without a
    definition of how 'application' is distinguished from 'website' or how duplicates
    are handled, this specific number appears to be an over-estimate or an unverified
    extrapolation from the raw video count.
- id: 41469ac2b9bc
  severity: science
  text: The statement that 'Human evaluation shows that the overall annotation accuracy
    exceeds 80%' (Introduction, paragraph 4) is unsupported by the provided text.
    The 'Data Quality Check' section (Section 5.4) only reports a Likert-scale user
    study (score 4.62/5) and inter-rater agreement, not a binary accuracy metric against
    a ground truth. This specific percentage is an over-claim not backed by the reported
    evidence.
- id: fb2aa7e07c95
  severity: writing
  text: The claim that the model 'surpasses state-of-the-art performance' (Abstract)
    is potentially misleading. Table 2 shows the proposed model (Mimo-VL-7B + WildGUI)
    scoring 67.6 on OSWorld-G, while Seed1.5-VL scores 62.9. However, Seed1.5-VL is
    a proprietary model, and the paper does not clarify if the comparison is fair
    regarding model size, training compute, or access to private data. The phrasing
    implies a universal SOTA without qualifying the proprietary nature of the competitor.
- id: 0ef7e7363a2e
  severity: writing
  text: The paper claims to process '500 million video metadata entries' (Abstract)
    but does not explicitly state the source or the time window of this data. Given
    the rapid evolution of YouTube content, the lack of temporal context for this
    massive dataset makes the claim of 'generalization' slightly over-reaching without
    specifying the data freshness.
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:10:43.901101Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the scale, quality, and performance impact of the proposed WildGUI dataset and Video2GUI framework. While the methodology is generally sound, there are instances where the authors extrapolate beyond the specific evidence provided in the text, particularly regarding specific numerical metrics and the definition of "state-of-the-art."

First, the claim in the Introduction that "Human evaluation shows that the overall annotation accuracy exceeds 80%" is a significant over-claim. The "Data Quality Check" section (Section 5.4) details a user study where experts rated data on a 1-5 Likert scale, achieving a mean score of 4.62. It does not report a binary accuracy metric (e.g., percentage of trajectories perfectly matching a ground truth). Conflating a high Likert score with a specific "80% accuracy" figure is not supported by the data presented and misrepresents the nature of the evaluation. This specific number should be removed or replaced with the actual metric reported (the Likert score).

Second, the claim that the dataset spans "over 1,500 applications and websites" (Abstract, Table 1) is presented as a definitive statistic. However, the paper does not describe the methodology used to count these unique entities. It is unclear if this count is derived from a unique string match of app names, a clustering of domains, or a manual verification process. Given the potential for noise in metadata (e.g., "Chrome" vs. "Google Chrome"), presenting this as a precise count without a definition of the counting protocol risks over-claiming the diversity of the dataset.

Third, the assertion that the method "surpasses state-of-the-art performance" (Abstract) requires nuance. In Table 2, the proposed model (Mimo-VL-7B + WildGUI) achieves 67.6 on OSWorld-G, surpassing Seed1.5-VL (62.9). However, Seed1.5-VL is a proprietary model, and the paper does not provide details on its training compute, data scale, or model size relative to the proposed 7B model. Claiming to surpass SOTA without qualifying that the comparison includes proprietary models with potentially different resource constraints can be seen as an over-extrapolation of the results' generalizability.

Finally, the claim of processing "500 million video metadata entries" is impressive but lacks temporal context. Without specifying the time window of the data collection, the claim of "generalization" to current real-world interfaces is slightly weakened, as GUI layouts and applications change rapidly. While this is a minor point, it contributes to the overall impression of over-reaching on the dataset's current relevance.

The authors should revise the text to align specific numerical claims (like the 80% accuracy) with the actual metrics reported in the experiments and clarify the definitions used for dataset statistics.
