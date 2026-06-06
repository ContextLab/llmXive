---
action_items:
- id: 50e7907410ba
  severity: science
  text: Multiple citations reference papers dated 2025-2026 (e.g., wang2025cut3r,
    xie2026scal3r, zhang2026loger, chen2026lingbotmap). The arXiv ID 2605.27367 suggests
    May 2026, a future date. Verify these are legitimate preprints and not fabricated
    citations.
- id: 24ed499777ed
  severity: science
  text: 'Abstract claims 19 datasets, 546 scenes, 41 models across 6 paradigms. Verify
    these counts match the actual tables (tab:datasets_summary, tab:main_leaderboard_filtered).
    Scene counts may differ across density regimes (Single: 179, Sparse: 129, Medium:
    129, Dense: 109).'
- id: 6d48e8487cec
  severity: science
  text: "Introduction claims +47%/+59% depth improvement and +3.1%/+5.5% pose improvement\
    \ for DA-Next vs DA3-Giant on sparse/medium inputs. Verify these percentages match\
    \ Tab. 5 (sparse: 0.095\u21920.050 AbsRel, medium: 0.086\u21920.035 AbsRel) and\
    \ pose metrics in the tables."
- id: 75e847141a7a
  severity: writing
  text: 'Table references need verification: Tab. 1 (benchmark_summary.tex) shows
    19 datasets but some entries are truncated. Ensure all cited datasets (e.g., Lingbot-Depth,
    RoboTwin, Xperience) have complete results in the per-dataset tables.'
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T10:34:08.544196Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

**Claim Accuracy Review**

**1. Citation Verification Concerns**

The bibliography contains numerous papers with publication years 2025-2026 (e.g., `wang2025cut3r`, `xie2026scal3r`, `zhang2026loger`, `chen2026lingbotmap`). Given the arXiv ID format (2605.27367 = May 2026), these represent future-dated publications that cannot be independently verified. Claims about these methods' capabilities (e.g., "TTT3R nearly doubles AUC@30") rely on citations that may not exist as described.

**2. Numerical Claim Consistency**

| Claim Location | Stated Value | Table Evidence |
|----------------|--------------|----------------|
| Abstract datasets | 19 | Tab. benchmark_summary shows 19 ✓ |
| Abstract scenes | 546 | Tab. benchmark_summary total: 179+129+129+109=546 ✓ |
| Introduction depth improvement | +47%/+59% | Sparse: 0.095→0.050 (47.4%); Medium: 0.086→0.035 (59.3%) ✓ |
| Introduction pose improvement | +3.1%/+5.5% | Requires verification in pose tables |

**3. Cross-Reference Accuracy**

- Figure 2 (geobench_combined.png) references scene categories but the caption mentions "median number of frames per scene" - verify this matches the actual figure content
- Table 3 (main_leaderboard_filtered) excludes \ours from rankings but includes it in results - clarify this distinction in the caption
- Appendix references (e.g., `appendix:dan`, `appendix:datasets`) should be verified for existence

**4. Data Support for Conclusions**

The claim "Egocentric-View and Wrist-View Remain the Dominant OOD Failure Modes" (Sec. 3) is supported by Fig. geobench_p3_auc30_domains.png showing performance drops. However, the specific training-data analysis cited needs verification against Tab. merged_dataset_usage_training_only.

**Recommendations**

1. Replace or verify all 2025-2026 dated citations with accessible, verifiable sources
2. Add explicit scene count disclaimers when reporting totals across density regimes
3. Clarify the \ours exclusion from rankings in Table captions
4. Ensure all 19 datasets have complete per-dataset results tables
