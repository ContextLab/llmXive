---
action_items:
- id: 337a7c7187ce
  severity: writing
  text: The abstract and main text claim code availability at a GitHub URL, but the
    repository is not provided in the input artifacts. For reproducibility, the specific
    commit hash or a permanent archive link (e.g., Zenodo) must be cited, and the
    code must be accessible to reviewers.
- id: e1884ded1ac6
  severity: writing
  text: The bibliography includes multiple entries with future dates (e.g., 2026)
    and arXiv IDs that do not resolve to public papers (e.g., 2606.18967). While this
    may be a preprint submission artifact, the data provenance of these citations
    is unclear. Verify that all external links and dataset references (e.g., SimpleRL,
    DAPO-Math) are stable and accessible.
- id: 0b9db888240a
  severity: writing
  text: The paper relies on external datasets (SimpleRL, ShareGPT, DAPO-Math) and
    model checkpoints (RedHatAI, MIT HAN Lab) without specifying exact version tags,
    commit hashes, or download scripts. To ensure schema and data integrity, the specific
    dataset versions and model commit hashes used for the experiments must be explicitly
    listed in the appendix or a data card.
artifact_hash: f5cd2bf8ec4b16de31454f2a2486d371422b77f233615f81a71aa09fed433b62
artifact_path: projects/PROJ-738-efficientrollout-system-aware-self-specu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T10:47:11.838961Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates strong technical depth regarding system-aware speculative decoding, but the data quality and provenance documentation require minor revisions to ensure full reproducibility and verifiability.

**Data Provenance and Version Control:**
The manuscript references several external datasets and model checkpoints critical to the evaluation, including `SimpleRL-8k-hard` (citing `zeng2025simplerl`), `ShareGPT` (citing `aeala2023sharegpt`), and `DAPO-Math-17K` (citing `yu2025dapo`). However, the text does not specify the exact version tags, commit hashes, or snapshot dates for these datasets. For instance, the `ShareGPT` dataset is known to have multiple unfiltered versions; without a specific commit or version identifier, the exact data distribution used for training the `Learned` baseline cannot be reconstructed. Similarly, the external model checkpoints (e.g., `RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3`) are cited with URLs but lack specific commit hashes or version numbers. Given the rapid evolution of these repositories, a specific commit hash is necessary to guarantee that the `block efficiency` metrics reported in Table 1 and the appendix are reproducible.

**External Link Stability and Link Rot:**
The abstract (line 14) and the bibliography contain URLs to GitHub repositories and arXiv preprints. The arXiv ID `2606.18967` cited in the provenance section corresponds to a future date (June 2026), which suggests these are placeholder or pre-submission identifiers. While acceptable for a preprint, the stability of the GitHub link provided in the abstract (`https://github.com/furiosa-ai/EfficientRollout`) must be verified. If the code is not yet public or is in a private state, the claim of "Code is available" is misleading. Furthermore, the bibliography includes several entries with 2026 publication years (e.g., `yue2026specattn`, `hu2026taming`). While these may be accepted papers, their current availability as open-access preprints or final versions should be confirmed to prevent link rot for reviewers attempting to verify the baselines.

**Schema and Metadata Completeness:**
The experimental setup (Appendix 3.1) describes the infrastructure (veRL v0.7.0, vLLM v0.11.2) and hardware (8x A100), which is good. However, the schema for the `SimpleRL` dataset split (Level 3-5 vs. Level 1-4) is described textually but not linked to a specific data manifest or hash. To fully satisfy data quality standards, a `data_card` or a `README` in the code repository should explicitly list the SHA-256 hashes of the dataset files used. Additionally, the `Learned` baseline relies on pre-trained EAGLE3 drafters; the paper notes that for Qwen models, they trained their own on ShareGPT. The specific hyperparameters and the exact split of ShareGPT used for this pre-training are not detailed, creating a gap in the data lineage for the baseline comparison.

**Recommendation:**
The authors should add a "Data and Code Availability" section in the appendix that lists:
1. Exact commit hashes for all external model checkpoints and datasets.
2. SHA-256 hashes for the specific dataset splits used.
3. A confirmation that the GitHub repository is public and contains the exact code used to generate the results in the paper.
4. Verification that all external URLs in the bibliography are currently active and point to the correct resources.
