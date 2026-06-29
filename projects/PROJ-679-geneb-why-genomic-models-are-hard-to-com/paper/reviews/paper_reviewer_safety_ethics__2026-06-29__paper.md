---
action_items:
- id: b8b5d5bdac1e
  severity: science
  text: "Add a dedicated discussion of dual\u2011use risks associated with large genomic\
    \ foundation models, including potential misuse for pathogenic genome design or\
    \ harmful gene drives, and outline concrete mitigation strategies (e.g., model\
    \ access controls, responsible release policies)."
- id: bd5f1c5d4332
  severity: science
  text: "Clarify the provenance and consent status of all training data, especially\
    \ any human genomic datasets, confirming that appropriate IRB/ethics approvals\
    \ and data\u2011use agreements are in place."
- id: 0b276211193a
  severity: writing
  text: Provide a statement on data privacy and security measures taken to protect
    any personally identifiable genetic information that may be present in the benchmark
    datasets.
- id: b434423c2fc5
  severity: writing
  text: "Disclose any potential conflicts of interest related to funding sources (e.g.,\
    \ Ministry of Economic Development of the Russian Federation) that could influence\
    \ the presentation or interpretation of safety\u2011related findings."
- id: af51528904c7
  severity: science
  text: Include recommendations for downstream users on responsible application of
    the benchmark results, emphasizing the need for ethical review before deploying
    models in clinical or ecological contexts.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:13:45.291309Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript introduces GENEB, a comprehensive benchmark evaluating 40 genomic foundation models across 100 tasks. While the technical contributions are solid, the safety and ethics aspects are insufficiently addressed.

**Dual‑use concerns** – Large DNA language models can be repurposed to design harmful genetic constructs (e.g., synthetic pathogens, gene drives). The paper’s impact statement briefly acknowledges “dual‑use research” but does not elaborate on concrete risks, mitigation, or governance. A dedicated section discussing these threats, model‑release policies, and possible safeguards (access controls, usage monitoring) is needed.

**Data provenance and consent** – The benchmark aggregates many public datasets, some of which contain human genomic sequences. The manuscript does not explicitly state that all data were obtained under appropriate IRB approvals or consent frameworks. Clarifying the ethical clearance for each dataset (especially any that include personally identifiable genetic information) is essential.

**Privacy and security** – No description is provided of how the authors protect sensitive genetic data during preprocessing, storage, or distribution of embeddings. Even if the data are public, best‑practice safeguards (de‑identification, secure storage) should be documented.

**Funding and conflict of interest** – The work is funded by a Russian governmental agency. While this does not inherently raise safety issues, transparency about any obligations or expectations tied to the funding (e.g., pressure to accelerate model deployment) would help readers assess potential bias.

**Guidance for downstream users** – Researchers who adopt the benchmark may fine‑tune or deploy the evaluated models in clinical, agricultural, or ecological settings. The paper should advise users to seek ethical review, consider regulatory constraints, and implement responsible AI practices before real‑world deployment.

Overall, the scientific content is sound, but the manuscript must strengthen its safety and ethics discussion to meet community standards for responsible AI in genomics.
