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
reviewed_at: '2026-06-08T19:33:23.506439Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

All three prior data quality action items remain unaddressed in this revision. First, the License column is still missing from all appendix tables (tab:appendix_s1 through tab:appendix_s8 in sections e002-e003). The tables catalog 30+ tools and datasets across the research lifecycle, yet provide no information about usage rights, licensing terms, or redistribution permissions. This is critical for practitioners who may wish to reuse these resources in their own work.

Second, mutable GitHub URLs persist throughout the bibliography and appendix tables. Examples include https://github.com/princeton-nlp/SWE-bench (tab:benchmarks, e000), https://github.com/Just-Curieous/Curie (tab:appendix_s1, e002), and https://github.com/guestrin-lab/deepscholar-bench (tab:appendix_s2, e002). These direct GitHub links are subject to repository deletion, renaming, or content changes, creating link rot risk for a survey paper intended as a stable reference. Archived versions via Zenodo, DOI, or a dedicated project index would provide citation stability.

Third, dataset and tool versions are not specified for most benchmarks. In tab:benchmarks (e000) and the appendix inventory tables, entries like "SWE-bench" (2024), "EXP-Bench" (2026), and "IdeaBench" (2024) lack version identifiers (e.g., v1.0, commit hash, snapshot date). Without version information, reproducibility is impossible—readers cannot know which exact dataset split or code version produced the reported results. This is especially critical for benchmarks that may have undergone updates since publication.

These three issues are fundamental to data provenance, reproducibility, and long-term usability of the survey's resource catalog. They should be resolved before acceptance.
