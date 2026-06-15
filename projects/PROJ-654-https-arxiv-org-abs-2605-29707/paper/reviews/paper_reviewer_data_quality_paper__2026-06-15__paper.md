---
action_items:
- id: 5fe7aca36d3f
  severity: writing
  text: Explicitly state the software license for the Domino code and model weights
    in the repository (e.g., MIT, Apache 2.0) to ensure legal reproducibility.
- id: 8e07f629fe70
  severity: writing
  text: Provide specific version tags or commit hashes for external links (GitHub,
    Hugging Face) to prevent link rot and ensure exact reproducibility of artifacts.
- id: 387f2d1f7c10
  severity: writing
  text: Clarify the discrepancy between training data in Section 6.1 (mlabonne/open-perfectblend)
    and Section 6.3 (ShareGPT) to ensure consistent data provenance reporting.
artifact_hash: ac9b2293924c2f0c1f04178796bb698ee01d07baef5d80d5250c3c91d8a5b9a5
artifact_path: projects/PROJ-654-https-arxiv-org-abs-2605-29707/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T01:03:00.400221Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses on data quality, provenance, and reproducibility artifacts. While the paper presents strong experimental claims, several data quality aspects require clarification to ensure long-term reproducibility and legal compliance.

**Data Provenance and Licensing**
The abstract and Appendix provide links to the code repository (`github.com/jianuo-huang/Domino`) and Hugging Face collection (`huggingface.co/collections/Huang2020/domino`), but no software license is specified in the manuscript or the linked resources' descriptions (as inferred from the text). Without an explicit license (e.g., MIT, Apache 2.0), the legal status of the released models and code remains ambiguous. Additionally, the training dataset `mlabonne/open-perfectblend` is cited in Section 6.1, but its license and the license of the *regenerated* responses (generated using Qwen3) are not discussed. Since Qwen3 has specific usage terms, the downstream license for the fine-tuned draft models must be clearly defined.

**Version Control and Link Rot**
External artifacts lack version pinning. Section 6.2 and Appendix Table `tab:baseline_checkpoints` list Hugging Face paths for baselines (e.g., `Angslim/Qwen3-4B_eagle3`) without specific revision IDs or commit hashes. Similarly, the GitHub link in the abstract has no tag. Model weights and datasets on these platforms can change or be deleted over time. To mitigate link rot, the authors should provide specific commit hashes or model revision IDs in a `README` or the paper's appendix.

**Data Consistency**
There is a discrepancy in reported training data. Section 6.1 states the main experiments use `mlabonne/open-perfectblend` (regenerated). However, Section 6.3 (Ablation) states: "The draft models are trained on ShareGPT". While retraining for ablation is methodologically sound, the text should explicitly clarify that the main results rely on PerfectBlend while ablation relies on ShareGPT to avoid confusion regarding the source of performance gains. The "same-data ablation" table caption (Table `tab:same-data-abl`) confirms ShareGPT usage for that specific table, but the distinction should be highlighted in the main text to ensure data lineage is clear.

**Schema**
The paper mentions regenerating responses for the training data but does not provide a schema or sample format for this processed dataset. Including a data card or schema definition in the repository would improve data quality transparency.

Addressing these points will significantly enhance the reproducibility and legal robustness of the work.
