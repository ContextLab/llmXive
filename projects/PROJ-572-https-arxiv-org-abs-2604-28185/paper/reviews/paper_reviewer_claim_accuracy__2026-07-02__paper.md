---
action_items:
- id: abcb7dc114e7
  severity: science
  text: Fig 1 caption claims 2025 contributed 188 papers (45.7%) of 411 post-2014
    refs. Bibliography contains 2026 citations (e.g., he2026gems). If 2026 refs are
    included, the 45.7% stat for 2025 is mathematically inconsistent. Recalculate
    stats or clarify the corpus cutoff date.
- id: 597185048f63
  severity: fatal
  text: Section 5.1 claims 'GPT 5.5 verified mismatches'. GPT 5.5 is not a released
    model. Citing a non-existent model as a factual verifier invalidates the stress
    test results. Correct to an existing model (e.g., GPT-4o) or remove the specific
    version.
- id: 2056b3063faa
  severity: writing
  text: Section 2.2 cites 2026 papers (e.g., HunyuanImage 3.0) as established facts
    with specific architecture details. Verify these are publicly available preprints
    and not speculative roadmaps. Qualify claims if sources are unreleased.
artifact_hash: 95c6cfb0cd885d3a15ec9e77a9e8d06788a35e40acba2d1245cdfd2be8660dc4
artifact_path: projects/PROJ-572-https-arxiv-org-abs-2604-28185/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:34:38.109043Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses strictly on the accuracy of factual claims and the validity of their supporting citations.

**Statistical Inconsistency in Publication Trends:**
In Section 1, the caption for Figure 1 states that 2025 contributed 188 papers (45.7%) out of 411 post-2014 references. However, the bibliography explicitly includes numerous citations dated **2026** (e.g., `he2026gems`, `feng2026gen`, `team2026longcat`). If the corpus includes 2026 papers, the total count of 411 and the specific percentage attributed to 2025 are mathematically inconsistent. The authors must clarify the exact cutoff date and recalculate the statistics to ensure the 45.7% figure accurately reflects the 2025 contribution relative to the total cited corpus.

**Citation of Non-Existent Models:**
In Section 5.1 ("The Metro Map Challenge"), the text claims: "GPT 5.5 verified mismatches in 9s". As of the current date, **GPT 5.5** has not been released by OpenAI. Citing a non-existent or unreleased model version as a factual benchmark verifier undermines the credibility of the stress test results. The authors must correct the model name to an existing version (e.g., GPT-4o) or provide a verifiable source for the "GPT 5.5" claim.

**Future-Dated Citations as Established Facts:**
The paper frequently cites works dated **2026** (e.g., `he2026gems`, `feng2026gen`) as if they are established, publicly available technical reports with specific architectural details (e.g., "80B/13B-active MoE"). While preprints can be future-dated, treating them as confirmed facts requires that the sources are actually accessible. If these are internal roadmaps or unreleased preprints, the claims regarding their specific architectures should be qualified as "reported" or "conjectured" rather than stated as definitive facts. The bibliography entries for these 2026 papers need to be verified for public availability.
