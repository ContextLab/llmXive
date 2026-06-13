---
action_items:
- id: e84d8051fe81
  severity: science
  text: Report variance for key diagnostic metrics in Figures 1-3 and Table 1 to establish
    statistical robustness beyond single-run observations.
- id: fe1837d45036
  severity: science
  text: Address the initialization confound in Section 4 where SFT updates are measured
    from pretrained Base while OPD and RLVR are from the SFT anchor.
- id: 0a06c3b84a07
  severity: science
  text: Provide sensitivity analysis for the rank-16 projection across different ranks
    to rule out cherry-picking the bottleneck dimension.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:55:28.374980Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical diagnostics regarding the geometry of on-policy distillation (OPD), particularly the functional sufficiency of low-dimensional subspaces in Section 5. However, the scientific evidence requires strengthening in three areas to support the central claims robustly.

First, statistical robustness is currently limited by the absence of variance reporting. Key results in Table 1 (update sparsity) and Figures 1-3 (spectral geometry, stable rank trajectories) present single-point estimates without error bars or standard deviations across seeds. While the Multi-seed variant is listed in Appendix Table 6, its results are not visualized in the main analysis. For claims about consistent positioning between SFT and RLVR, demonstrating low variance across seeds is critical to rule out run-specific artifacts.

Second, the comparison of SFT, OPD, and RLVR geometries in Section 4 suffers from an initialization confound. The SFT update is computed from the pretrained Base checkpoint while OPD and RLVR updates are computed from the SFT anchor. Since the magnitude and spectral properties of updates often depend heavily on the initialization stage, the claim that OPD occupies an intermediate regime between SFT and RLVR may be confounded by the different training phases rather than the algorithmic paradigm alone. A controlled comparison where all three paradigms start from the same checkpoint would isolate the algorithmic effect more cleanly.

Third, the choice of rank-16 for the functional sufficiency test in Section 5.2 appears post-hoc, motivated by the observed stable rank. While Appendix Figure 6 shows consistency across benchmarks, a sensitivity analysis across projection ranks within the main text would strengthen the claim that the subspace is inherently low-dimensional rather than just sufficiently low-dimensional at that specific rank. Addressing these points will significantly improve the evidentiary support for the proposed geometric theory.
