---
action_items:
- id: 3159f0f79d4d
  severity: writing
  text: Specify the exact Creative Commons license identifier (e.g., CC-BY-4.0) in
    the Ethics statement instead of the generic 'CC'.
- id: 58fa2c32c009
  severity: science
  text: Include a specific commit hash or version tag for the dataset release to ensure
    reproducibility of the 307-task benchmark.
- id: 1c5bf7bc1b63
  severity: writing
  text: Clarify IRB approval or informed consent procedures for the 8 PhD-level human
    annotators mentioned in Section 'Human Annotation Details'.
artifact_hash: 4c1448d6284f48048906ba145a0a228414d922f3ed6467261dd793143d8d0ecf
artifact_path: projects/PROJ-668-https-arxiv-org-abs-2606-05622/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T08:40:36.879952Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a substantial dataset of 307 household tasks with 240 human-annotated trajectories, demonstrating strong commitment to data quality through multi-turn validation and LLM-human alignment checks (Section: Human Annotation Details). However, several metadata and provenance issues require attention to ensure long-term usability and reproducibility.

First, the **license specification** in the Ethics statement is insufficient. The text states "benchmark under CC" without specifying the version (e.g., CC-BY-4.0, CC0). This ambiguity hinders downstream reuse and compliance checking. Please update the Ethics statement to explicitly name the license identifier.

Second, **version control** for the data is missing. While a GitHub repository and HuggingFace dataset link are provided (Critical Elements list), the manuscript does not cite a specific commit hash or dataset version tag. Given the dynamic nature of LLM-generated benchmarks, a frozen version is critical for reproducibility. Please add a version tag (e.g., v1.0) or commit hash to the data availability statement.

Third, **model provenance** for data generation is vague. The Environment Construction Algorithm (Section: Formalization) relies on LLMs (GPT-4.1, DeepSeek-V3.2, etc.) to generate constraints. The specific API versions or model checkpoints used for this generation are not detailed. Since the benchmark quality depends on these generators, their exact versions should be documented to allow replication of the data creation pipeline.

Finally, regarding **human data**, the paper mentions 8 PhD-level annotators but does not explicitly state whether IRB approval was obtained or if informed consent was secured. While this is often standard for academic research, explicit confirmation in the Ethics statement is required for data quality compliance regarding human subjects.

Addressing these points will significantly improve the data quality metadata and ensure the benchmark remains a reliable resource for the community.
