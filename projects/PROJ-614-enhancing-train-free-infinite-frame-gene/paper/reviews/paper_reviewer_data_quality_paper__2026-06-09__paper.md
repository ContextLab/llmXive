---
action_items:
- id: 7c02ab3093c4
  severity: writing
  text: The paper lacks explicit license information for VBench, NarrLV, and foundation
    models (VideoCrafter2, Wan2.1). Add a data availability statement specifying licenses
    for all external datasets and models used.
- id: b8b8f752539d
  severity: writing
  text: No version numbers are specified for VBench or NarrLV benchmarks. Include
    version identifiers or commit hashes to ensure reproducibility of evaluation results.
- id: 1645e314732f
  severity: writing
  text: The project page URL (https://xiaokunfeng.github.io/miga_homepage/) in the
    abstract has no archival guarantee. Consider adding an arXiv snapshot or DOI for
    permanent access.
- id: 68319942ac43
  severity: writing
  text: Evaluation data (VBench/NarrLV prompts, data splits) are not described with
    sufficient detail. Add a data card appendix specifying prompt counts, split sizes,
    and any preprocessing applied.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T21:46:33.362848Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review confirms that all four data quality action items from the previous cycle remain unaddressed in the current revision. The manuscript continues to lack critical provenance and reproducibility details required for a train-free method relying on external benchmarks and models.

1. **Licensing (Item 7c02ab3093c4):** The Conflict of Interest Disclosure (Section 1) mentions Wan2.1 is open-source from Tongyi Lab but omits the specific license (e.g., Apache 2.0, CC-BY). Similarly, VBench and NarrLV licenses are not stated anywhere in the text or Appendix. A formal Data Availability Statement is absent.

2. **Version Control (Item b8b8f752539d):** In Section 4.1 (Implementation Details), the authors cite `huang2024vbench` and `feng2025narrlv` but do not specify version numbers, commit hashes, or release dates. Without this, the evaluation results cannot be precisely reproduced, as benchmark metrics often evolve.

3. **Link Rot (Item 1645e314732f):** The Abstract includes the project URL `https://xiaokunfeng.github.io/miga_homepage/`. This domain has no archival guarantee. While the paper is on arXiv, the supplementary material linked on the project page should have a DOI or snapshot reference to ensure long-term accessibility.

4. **Data Splits (Item 68319942ac43):** Section 4.1 mentions using "evaluation prompts with Temporal Narrative Atom (TNA) counts of 2, 3, and 4" for NarrLV but does not provide a data card appendix detailing the exact prompt counts, dataset splits, or preprocessing steps used for VBench/NarrLV evaluation. This omission hinders independent verification of the reported SOTA performance.

No new data quality issues were identified, but the persistence of these four items prevents acceptance. Please address these documentation gaps to ensure the work meets community standards for reproducibility and data provenance.
