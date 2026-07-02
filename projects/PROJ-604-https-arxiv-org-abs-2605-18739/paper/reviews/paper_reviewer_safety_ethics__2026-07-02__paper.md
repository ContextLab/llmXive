---
action_items:
- id: e8223a51c045
  severity: writing
  text: 'The paper presents a significant technical advancement in long video generation
    infrastructure but lacks necessary depth in its safety and ethical disclosures.
    Broader Impacts and Dual-Use Risks: The "Broader Impacts" section (Conclusion)
    is critically underdeveloped. The authors state that the infrastructure "involves
    no negative social implications" and simply "shares the ethical impacts with existing
    video generation models." This is a dangerous oversimplification. LongLive-2.0''s
    specific cap'
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:01:38.746826Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a significant technical advancement in long video generation infrastructure but lacks necessary depth in its safety and ethical disclosures.

**Broader Impacts and Dual-Use Risks:**
The "Broader Impacts" section (Conclusion) is critically underdeveloped. The authors state that the infrastructure "involves no negative social implications" and simply "shares the ethical impacts with existing video generation models." This is a dangerous oversimplification. LongLive-2.0's specific capabilities—real-time (45.7 FPS), interactive, multi-shot generation—significantly lower the barrier for creating high-quality, coherent deepfakes and disinformation campaigns. The ability to switch prompts mid-generation and maintain subject consistency (as highlighted in the "Multi-Shot Attention Sink" section) directly facilitates the creation of convincing synthetic media for malicious purposes. The manuscript must explicitly discuss these dual-use risks and propose concrete mitigation strategies (e.g., watermarking, detection mechanisms, or usage policies) rather than deferring the issue to "existing models."

**Data Privacy and Consent:**
In the Appendix section "Multi-shot Long-video Dataset," the authors describe curating 120K long videos and filtering for quality (e.g., removing logos/watermarks). However, there is no mention of how the dataset was sourced, whether it complies with copyright laws, or if the individuals depicted in the videos provided consent for their likeness to be used in training a generative model. Given the increasing regulatory scrutiny on AI training data (e.g., GDPR, EU AI Act), the absence of a data governance statement, consent protocol, or reference to an ethics review board (IRB) is a significant omission. The authors should clarify the provenance of the data and the measures taken to ensure privacy and legal compliance.

**Conclusion:**
While the technical contributions are sound, the paper fails to adequately address the societal implications of its high-efficiency, real-time generation capabilities. A revision is required to expand the "Broader Impacts" section with specific risk analysis and to provide transparency regarding data sourcing and consent.
