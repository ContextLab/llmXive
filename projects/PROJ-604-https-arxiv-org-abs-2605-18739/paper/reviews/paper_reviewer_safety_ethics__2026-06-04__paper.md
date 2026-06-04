---
action_items:
- id: 99bb5e822075
  severity: writing
  text: The Broader Impacts section (Conclusion) states the infrastructure 'involves
    no negative social implications,' which is inadequate for a video generation system.
    Expand to explicitly discuss dual-use risks (deepfakes, misinformation) and mitigation
    strategies.
- id: 53dcee6f7971
  severity: writing
  text: No discussion of training data provenance or consent. The dataset section
    (Appendix) describes 120K videos but does not address whether subjects consented
    to inclusion or if copyrighted material was used. Add data sourcing and privacy
    considerations.
- id: fa805b309554
  severity: writing
  text: No content safety measures are described. Video generation models require
    safeguards against harmful content generation. Include discussion of safety filters
    or content moderation approaches in deployment.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T18:58:13.688481Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety and ethics considerations for LongLive-2.0.

**Broader Impacts Statement (Insufficient):** The Conclusion's Broader Impacts section (lines 512-514) states that "The NVFP4 and parallelism infrastructure itself involves no negative social implications." This is overly dismissive for a video generation system. While the infrastructure component may be neutral, the underlying video generation capability carries well-documented risks including deepfakes, misinformation, and non-consensual content. The broader impacts statement should explicitly acknowledge these risks and discuss any mitigation strategies (e.g., watermarking, content filters, usage policies) that accompany deployment.

**Data Privacy and Consent (Missing):** The Appendix section "Multi-shot Long-video Dataset" describes curating 120K long videos with structured captions but provides no information about data provenance, consent, or copyright considerations. For safety and ethics compliance, the authors should clarify: (1) whether individuals appearing in the videos consented to inclusion, (2) whether the dataset includes copyrighted material and how this was addressed, and (3) whether any personally identifiable information was removed. This is particularly important given the interactive nature of the generation system.

**Content Safety Measures (Absent):** There is no discussion of content safety measures throughout the paper. Video generation models require safeguards to prevent generation of harmful content (violence, harassment, deceptive media). The authors should describe whether safety filters, content moderation, or usage restrictions are implemented or planned for deployment.

These concerns are fixable through manuscript revisions without requiring new experiments. The technical contributions remain valid, but the safety and ethics documentation requires strengthening before publication.
