---
action_items:
- id: 7c1ba8b3a6cb
  severity: writing
  text: The paper acknowledges dual-use risks (impersonation) only in Limitations.
    Expand this discussion in the main text to include potential mitigation strategies
    for downstream users (e.g., watermarking, disclosure requirements).
- id: 486d8b04cd00
  severity: science
  text: The dataset includes probes derived from Harry Potter (copyrighted). Releasing
    these under CC-BY-4.0 may infringe copyright. Clarify the legal basis for public
    release or restrict access to the copyrighted subset.
- id: d50b01bd0e0d
  severity: writing
  text: Appendix mentions one human study was 'non-compensated'. Ensure this aligns
    with institutional IRB/ethics guidelines regarding research labor, even for colleagues.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T09:52:31.063000Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This paper presents a novel benchmark for evaluating character arc consistency in role-playing language agents. From a safety and ethics perspective, the authors have made commendable efforts to address human subjects research. The IRB statement in Appendix `app:arc-details` explicitly clarifies that the annotation tasks did not constitute human subjects research, citing the lack of PII and the voluntary nature of participation. Informed consent is mentioned for both the axis validation and judge plausibility studies.

However, there are areas requiring attention before publication. First, the dual-use risk of high-fidelity role-playing agents is significant. While the Limitations section notes that "Higher-fidelity role-playing agents may also enable more credible impersonation," this critical safety concern is relegated to the end of the paper. Given the benchmark's goal of improving character fidelity, a more prominent discussion in the main text regarding potential misuse (e.g., social engineering, misinformation) and recommended mitigations (e.g., output watermarking, usage policies) is necessary.

Second, the data licensing presents a potential legal and ethical conflict. The dataset includes 17 novels, one of which is *Harry Potter* (non-Gutenberg, copyrighted). The authors state the artifacts will be distributed under CC-BY-4.0. Releasing derivative works of copyrighted text under a permissive license may infringe on the original copyright holders' rights. The authors should clarify the legal basis for this release or restrict the public distribution of probes derived from copyrighted materials to avoid facilitating copyright infringement.

Finally, regarding annotator labor, Appendix `app:judge-crossval-human` states that annotators for the judge plausibility study were "colleagues who contributed on a non-compensated basis." While voluntary, research ethics guidelines often recommend fair compensation for all research labor to avoid exploitation, even among colleagues. The authors should confirm this practice aligns with their institution's specific ethics policies.

Overall, the paper is ethically sound in its human subjects handling but requires clarification on data licensing and a stronger emphasis on dual-use risks.
