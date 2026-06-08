---
action_items:
- id: f29d449beaa9
  severity: writing
  text: Add a License column to all appendix tables (e.g., tab:appendix_s1) to specify
    usage rights for tools and datasets.
- id: ded46566c806
  severity: writing
  text: Replace mutable GitHub URLs with archived versions (Zenodo/DOI) or link to
    a stable project index to prevent link rot.
- id: 5d2e597c6bb7
  severity: writing
  text: Specify dataset/tool versions (e.g., v1.0, commit hash) for all benchmarks
    to enable reproducibility.
artifact_hash: 406e68578ff634bb909200355e48bd438ba9dc41c31d75ef24170dcb14dc58cd
artifact_path: projects/PROJ-602-https-arxiv-org-abs-2605-18661/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T05:15:33.675746Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides a comprehensive taxonomy of AI research tools, but the data quality of the referenced resources requires improvement for reproducibility and long-term utility. In the Appendix tables (e.g., `tab:appendix_s1`, `tab:appendix_s3`), columns for `GitHub`, `Link`, and `Venue` are present, but critical metadata such as software **license** and **dataset version** are absent. For instance, `tab:appendix_s1` lists `IdeaBench` and `SWE-bench` but does not specify their usage licenses (e.g., MIT, CC-BY, Apache 2.0). This omission prevents downstream users from understanding legal constraints on reusing these benchmarks or tools.

Furthermore, the reliance on dynamic external links poses a significant link rot risk. While the authors maintain a project page (`https://worldbench.github.io/awesome-ai-auto-research`), the hundreds of third-party GitHub URLs (e.g., `https://github.com/SakanaAI/AI-Scientist` in `tab:appendix_e2e`) are not archived. Best practice for survey papers involves providing DOIs or Zenodo archives for code repositories to ensure long-term accessibility independent of platform availability. The current `2026` dates in citations (e.g., `arXiv'26`) suggest a future cutoff; if these are preprints, their stability is higher, but final publication versions should be linked once available.

Version control is also inconsistent. Some entries mention versions (e.g., `SWE-bench_Verified`), while others list only the year (e.g., `arXiv'24`). Without specific commit hashes or dataset release versions, it is difficult to reproduce the exact state of the tools evaluated. Additionally, missing data in tables is denoted by `-` (e.g., `tab:appendix_s1`, row 7), which is acceptable but should be explicitly defined in a footnote to distinguish between "not available" and "not applicable" to avoid confusion.

To improve data quality, the authors should:
1. Add a `License` column to the appendix tables for all listed tools and datasets.
2. Replace mutable GitHub URLs with archived versions (Zenodo/DOI) where possible, or link to the project page as a central stable index.
3. Specify dataset/tool versions (e.g., v1.0, commit hash) for all benchmarks to enable reproducibility.
4. Clarify the meaning of `-` in tables with a footnote.

These changes will ensure the survey remains a reliable, reproducible reference as the field evolves and links potentially decay.
