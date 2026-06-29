---
action_items:
- id: c10c2e730ad9
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and jargon that
    are not consistently defined for a general machine learning audience. In Section
    2, the term "POMDP" is introduced and immediately used as an acronym without spelling
    out "Partially Observable Markov Decision Process" first, which excludes readers
    from adjacent fields. Similarly, in Section 3.2, the phrase "VLM-driven" assumes
    familiarity with the acronym "VLM" (Vision-Language Model); this should be expanded
    to "vision-la
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:21:31.037472Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are not consistently defined for a general machine learning audience. In Section 2, the term "POMDP" is introduced and immediately used as an acronym without spelling out "Partially Observable Markov Decision Process" first, which excludes readers from adjacent fields. Similarly, in Section 3.2, the phrase "VLM-driven" assumes familiarity with the acronym "VLM" (Vision-Language Model); this should be expanded to "vision-language model-driven" upon first mention.

In Section 5.1, the term "SFT" is used to describe the second training stage without definition; it should be written as "supervised fine-tuning (SFT)" initially. The Appendix introduces "MSE" in the context of loss functions without defining it as "mean squared error." Additionally, Table 2 and Section 5.2 utilize "SR" for "Success Rate" without prior expansion in the text or caption.

The term "omnimodal" is used in Section 3.1 to describe the scoring model. This is not a standard term in the field and should be replaced with "multimodal" or a descriptive phrase like "supporting text, video, and audio inputs." The phrase "grounding-friendly" in Section 3.2 is also informal jargon; "optimized for spatial grounding" would be more precise. Finally, the repeated use of "coarse-to-fine" in Section 3.1, while common in computer vision, should be briefly contextualized or replaced with "progressive filtering" to ensure clarity for readers unfamiliar with this specific algorithmic pattern. These changes are necessary to ensure the paper is accessible to the broader ICML community.
