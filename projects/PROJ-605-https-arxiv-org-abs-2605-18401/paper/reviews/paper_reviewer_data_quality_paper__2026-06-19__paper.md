---
action_items:
- id: 61d5425e0800
  severity: fatal
  text: "Add an explicit statement of the license under which the million\u2011scale\
    \ skill corpus is collected and redistributed (e.g., MIT, Apache\u20112.0). Without\
    \ this the provenance and reuse legality are unclear."
- id: 151abc5a3571
  severity: writing
  text: Provide a concrete schema (e.g., JSON Schema) for the three artifact types
    (Recommendation, Attribution, Evolution) in the main text or an appendix, and
    reference it where the prompts are described.
- id: f98e27bffeff
  severity: science
  text: Document how missing or malformed fields in the collected SKILL.md files are
    detected and handled (e.g., default values, exclusion criteria). The current description
    of profiling is vague.
- id: b169bdd4862a
  severity: writing
  text: "Include a version\u2011control strategy for the evolving skill library (e.g.,\
    \ git commit hashes, timestamps) and explain how updates are tracked across offline/online\
    \ evolution cycles."
- id: b5798f3659cc
  severity: writing
  text: "Verify all external URLs in the bibliography (e.g., https://agentskills.io/,\
    \ https://github.com/harbor-framework/harbor) and add a \u201Clast\u2011accessed\u201D\
    \ date; consider providing archived copies (e.g., via Internet Archive) to mitigate\
    \ link rot."
artifact_hash: fcaf17c52a220725cfb9e8a31b0ca110c5bf54bf4640262b3d2d168e2f060f9e
artifact_path: projects/PROJ-605-https-arxiv-org-abs-2605-18401/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-19T13:47:57.425054Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript introduces a lifecycle framework for “Agent Skills” and reports impressive gains on Terminal‑Bench 2.0 and SWE‑Bench Pro. From a data‑quality perspective the paper defines three structured artifact schemas (Recommendation, Attribution, Evolution) and uses them throughout the experiments, which is a strong point. However, several critical provenance and reproducibility details are missing or under‑specified.

First, the paper states that a “million‑scale open‑source skill corpus” is aggregated from GitHub SKILL.md files, yet it does not disclose the licensing terms of the harvested content. Without an explicit license statement, downstream users cannot be sure whether redistribution or modification of the skill library is permissible, which undermines the legal provenance of the dataset (see Section 3.1). An explicit license (or a statement that the corpus is used under fair‑use with attribution) should be added.

Second, while the schema for each artifact is described in prose (e.g., Section 2.2), no formal schema (such as JSON Schema) is provided. A concrete schema would make it easier for other researchers to validate generated artifacts and would improve interoperability. Including the schema in an appendix would also aid reviewers in checking that the reported JSON outputs conform to the intended structure.

Third, the handling of missing or noisy data in the collected skills is not discussed. Real‑world SKILL.md files often lack required fields (e.g., runtime requirements, verifiability tags). The paper should describe any validation pipeline, default fall‑backs, or exclusion criteria applied during profiling, as this directly impacts the quality of the recommendation and evolution stages.

Fourth, the evolution process mentions “evidence‑gated updates” and “conservative library updates,” but the version‑control mechanism is opaque. It is unclear whether updates are tracked via git commits, timestamps, or a custom metadata store. Providing a brief description of how skill versions are identified, stored, and retrieved would greatly enhance reproducibility.

Finally, the bibliography contains many URLs to resources that are expected to exist in 2026 (e.g., https://agentskills.io/, https://github.com/harbor-framework/harbor). While these are reasonable citations, the paper should record the date each URL was last accessed and, if possible, archive a snapshot (e.g., via the Internet Archive) to guard against future link rot.

Addressing these points will solidify the data provenance, licensing, and reproducibility of the SkillsVote framework, making the contribution more robust for the community.
