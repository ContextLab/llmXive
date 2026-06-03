---
action_items:
- id: 7ecf0d476405
  severity: writing
  text: Provide a comprehensive table listing the license type and version for every
    dataset used in the pretraining mixture (e.g., Ego4D, EPIC-KITCHENS, BridgeData).
- id: 8ed31b917c02
  severity: writing
  text: Replace unstable blog post URLs (e.g., RoboInF blog) with persistent identifiers
    (DOIs) or archived versions to prevent link rot.
- id: 30aa186ff10c
  severity: writing
  text: Include a data card or datasheet for the Qwen-VLA pretraining corpus detailing
    composition, filtering criteria, and known biases.
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T04:50:08.350559Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale data mixture for training Qwen-VLA but lacks sufficient transparency regarding data provenance, licensing, and versioning, which are critical for reproducibility and legal compliance in foundation model research. 

In Section 3.2.1 ("Egocentric Human Data"), datasets like Ego4D, EPIC-KITCHENS, EgoDex, EgoVerse, and Xperience are cited. However, the specific licenses (e.g., CC-BY, non-commercial restrictions) for each are not provided. Without this, users cannot determine if the resulting model weights are legally redistributable or compatible with downstream commercial use. Similarly, Section 3.2.2 ("Synthetic Simulation Data") references `RoboInF` via a blog post URL (`https://xlang.ai/blog/roboinf`). Relying on blog posts introduces significant link rot risk; stable archival links or DOIs should be used for long-term reproducibility.

Section 3 ("Large-Scale Joint Pretraining") describes the data mixture percentages (e.g., "6.0% of the total pretraining mixture" for egocentric data) but does not provide dataset version numbers (e.g., R2R v1.0 vs v2.0, LIBERO split versions). This hinders exact reproduction of the training splits and evaluation benchmarks. Furthermore, there is no reference to a "data card" or "datasheet" for the Qwen-VLA pretraining corpus, which is standard practice for transparency on data composition and biases in large-scale models.

Data cleaning procedures in the "Vision-language data" section mention removing "anomalous lengths" but do not quantify thresholds (e.g., minimum/maximum frame counts). Providing these hyperparameters would improve reproducibility of the filtering pipeline. Evaluation data in Section 5 (e.g., R2R, RxR) also lacks version specification, making it difficult to verify if the correct validation splits were used.

To address these concerns, please add a dataset license table, replace volatile URLs with persistent identifiers, and publish a datasheet for the pretraining mixture detailing composition and filtering logic.
