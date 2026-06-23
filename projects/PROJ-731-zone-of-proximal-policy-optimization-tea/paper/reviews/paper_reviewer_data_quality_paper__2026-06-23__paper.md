---
action_items:
- id: a0cd25a806aa
  severity: writing
  text: "Add an explicit Data Availability statement that describes where the ZPPO\u2011\
    77K multimodal RL corpus can be accessed, includes a persistent identifier (e.g.,\
    \ DOI or Zenodo record), and specifies the license under which the data are released."
- id: 1148890d6b4e
  severity: writing
  text: "Provide a Code Availability statement with a link to a public repository\
    \ (e.g., GitHub) that contains the training scripts, model checkpoints, and evaluation\
    \ code, and clearly state the software license (e.g., Apache\u20112.0, MIT)."
- id: a996779ceeb1
  severity: writing
  text: Archive all external URLs referenced in the paper (project page, HuggingFace
    dataset links, figure PDFs) using a service such as archive.org or Zenodo, and
    include the archived URLs to mitigate future link rot.
- id: '169006967587'
  severity: writing
  text: Document the version of each external resource used (e.g., specific commit
    hash of the HuggingFace dataset, version tag of the teacher model) to ensure reproducibility.
- id: 466aacbb7865
  severity: writing
  text: "If the paper relies on any proprietary or non\u2011open datasets, explicitly\
    \ state the licensing terms and any usage restrictions."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:03:32.276250Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel RL‑based distillation technique (ZPPO) but provides limited information about the underlying data assets and software artifacts, which hampers reproducibility and long‑term accessibility.  

1. **Data provenance and licensing** – The core training set, “ZPPO‑77K multimodal RL corpus,” is mentioned (Section 3, “Setup”) without any citation, URL, or identifier. No license (e.g., CC‑BY, CC0) is declared, leaving readers uncertain about redistribution rights. Moreover, the benchmark tables reference numerous external datasets (e.g., MVision, AIME25, MMVU) via HuggingFace repository names, but the exact revisions (commit hashes or release tags) are omitted, making it impossible to reconstruct the exact evaluation splits used.  

2. **Code and model availability** – The paper describes a complex training pipeline (Algorithm 1, hyper‑parameter tables) yet does not provide a link to source code, model checkpoints, or scripts for reproducing the BCQ/NCQ prompt generation and replay buffer logic. The absence of a software license further prevents downstream use.  

3. **Version control and reproducibility** – Hyper‑parameter values are listed (Table “Training hyperparameters”), but there is no indication of the configuration files or the exact version of the underlying GRPO/DAPO implementations. The paper cites many recent arXiv preprints (e.g., \citep{shao2024deepseekmath}) without version numbers, which could change over time.  

4. **Link rot risk** – The project page URL (https://byungkwanlee.github.io/ZPPO-page/) and several HuggingFace dataset links (e.g., https://huggingface.co/datasets/zlab-princeton/Vero-600k) are included without archival backups. If these resources disappear, the empirical claims become unverifiable.  

5. **Schema and missing‑data handling** – The evaluation protocol relies on a “rule‑based reward grader” that parses LaTeX boxed answers; however, the handling of malformed or missing outputs is only briefly mentioned (“malformed output scores 0”). A more formal description of how missing or ambiguous predictions are treated would improve data integrity.  

**Recommendations**: The authors should augment the manuscript with explicit data and code availability statements, include persistent identifiers (DOI, archive URLs) for all external resources, specify licenses, and provide versioned references (commit hashes or release tags). Archiving the project page and dataset links will safeguard against future link rot. Clarifying the handling of missing or malformed outputs will strengthen the data schema. Addressing these points will bring the paper into compliance with community standards for data quality and reproducibility.
