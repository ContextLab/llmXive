---
action_items:
- id: c90213e4b5d5
  severity: writing
  text: The paper cites a GitHub repository (https://github.com/jinyangwu/OPID/tree/main)
    in the summary but fails to include a formal license declaration for the code
    or the dataset artifacts. Without an explicit license (e.g., MIT, Apache 2.0)
    in the repository or a statement in the 'Implementation Details' section (Appendix
    A.3), the provenance and reuse rights of the training data and analyzer prompts
    are unclear.
- id: 99bea3658946
  severity: writing
  text: The 'Datasets' table in Appendix A.1 lists specific train/test split counts
    (e.g., 19,200 train samples for Search-based QA) but does not cite the specific
    version or commit hash of the underlying benchmark datasets (e.g., Search-R1,
    Natural Questions). Given the dynamic nature of web-based QA datasets, the lack
    of version control identifiers risks link rot and irreproducibility of the exact
    data distribution used.
- id: e8a0762b4798
  severity: writing
  text: The 'Trajectory analyzer' section (Appendix A.3) relies on an external API
    (GLM-5.2) to generate skills. The paper does not specify the data retention policy,
    privacy guarantees, or terms of service compliance for sending agent trajectories
    to this external service. This creates a potential data provenance gap regarding
    the origin of the 'hindsight skills' used for distillation.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:05:39.872309Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates a strong methodological contribution but exhibits significant gaps in data quality documentation, specifically regarding provenance, licensing, and external dependency management.

First, while the paper references a GitHub repository for the code (`https://github.com/jinyangwu/OPID/tree/main`), there is no explicit mention of the software license governing the code or the generated artifacts (skills, prompts) in the text or the repository metadata summary. For a method relying on distillation, the license of the training data (the generated skills) is critical for downstream reuse. The absence of a license statement (e.g., MIT, Apache 2.0) in the 'Implementation Details' (Appendix A.3) or the repository link description renders the artifact's legal status ambiguous.

Second, the dataset provenance lacks version control. Appendix A.1, Table 1, lists sample counts for benchmarks like ALFWorld and Search-based QA but does not specify the exact dataset versions, commit hashes, or download dates. Benchmarks like Natural Questions or WebShop can undergo silent updates or have different splits available. Without these identifiers, the exact data distribution used for the reported 19,200 training samples cannot be precisely reconstructed, increasing the risk of link rot and irreproducibility.

Third, the data pipeline relies on an external LLM API (GLM-5.2) for the 'Trajectory analyzer' (Appendix A.3). The paper does not address the data provenance implications of sending agent trajectories to a third-party service. There is no statement regarding data retention, privacy, or whether the generated skills are considered derivative works of the external model's output. This creates a "black box" in the data generation chain, making it difficult to audit the quality or origin of the supervision signal.

Finally, the external links to benchmarks (e.g., Search-R1) and the code repository are not accompanied by archive identifiers (like DOIs or Zenodo links) in the bibliography or text, leaving the project vulnerable to link rot. The authors should add a "Data Availability" section explicitly stating licenses, dataset versions, and archival links for all external resources.
