# Calibration adjudication — domain: (unspecified)
<!-- runner_version: 848334e6 -->

**Summary**: 1 of 1 injections caught · 0 missed · 23 extra finding(s) on clean artifacts (each flagged for manual adjudication).

**Runner version**: `848334e6`

Per design SSoT (FR-046): adjustment is DIFFERENTIAL + manual. There is no fixed over-flag % threshold; the maintainer reviews each extra finding below and marks it 'legitimate' (panel correctly noticed real flaw in a supposedly-clean sample → fix the sample) or 'spurious' (prompt over-strict → adjust the prompt).

## 1. Injector: `nonexistent_citation`

- **Expected lens**: `claim_accuracy`
- **Description**: Injector: nonexistent_citation
- **Status**: ✅ CAUGHT
- **Lenses flagged on injected**: claim_accuracy, figure_critic, scientific_evidence, writing_quality

### Extra findings on the CLEAN artifact (23) — needs adjudication

- `claim_accuracy` [writing] `(unstated)` — Tibshirani 1996 DOI '10.1111/j.2517-6161.1996.tb02080.x' should be verified against the official publication record. The Lasso paper appeared in JRSS B, but this specific DOI format requires confirmation to ensure citation accuracy.
- `claim_accuracy` [writing] `(unstated)` — Claim 'correctly identifies the Lasso paper as a positive contribution under all of its lenses' is a result claim that requires supporting evidence (e.g., quantitative metrics or explicit panel verdicts). Consider adding specific evaluation numbers or removing the absolute 'all' qualifier.
- `scientific_evidence` [science] `(unstated)` — Paper lacks empirical scientific evidence: no sample sizes, no statistical tests, no effect sizes, no controls or replication reported. This lens cannot evaluate claims without quantitative research design.
- `writing_quality` [writing] `(unstated)` — Full paper LaTeX source not provided. Only synthetic seed excerpt (1 paragraph) available for review. Cannot assess overall writing quality without complete manuscript.
- `figure_critic` [writing] `(unstated)` — 
- `figure_critic` [writing] `(unstated)` — 
- `claim_accuracy` [writing] `paper/source/main.tex` — Tibshirani 1996 DOI '10.1111/j.2517-6161.1996.tb02080.x' should be verified against the official publication record. The Lasso paper appeared in JRSS B, but this specific DOI format requires confirmation to ensure citation accuracy.
- `claim_accuracy` [writing] `paper/source/main.tex` — Claim 'correctly identifies the Lasso paper as a positive contribution under all of its lenses' is a result claim that requires supporting evidence (e.g., quantitative metrics or explicit panel verdicts). Consider adding specific evaluation numbers or removing the absolute 'all' qualifier.
- `scientific_evidence` [science] `paper/source/main.tex:1-10` — Paper lacks empirical scientific evidence: no sample sizes, no statistical tests, no effect sizes, no controls or replication reported. This lens cannot evaluate claims without quantitative research design.
- `figure_critic` [writing] `paper/source/main.tex` — Prior concern figure_critic-63ecfb3d remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `paper/source/main.tex` — Prior concern figure_critic-03490872 remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `paper/source/main.tex` — No figures present in paper/source/main.tex for evaluation. Per R3 rules, this lens cannot assess figure quality when no figures exist. Pipeline requires tasks.md to generate figure artifacts.
- `scientific_evidence` [science] `paper/source/main.tex:1-10` — Paper lacks empirical scientific evidence: no sample sizes, no statistical tests, no effect sizes, no controls or replication reported. This lens cannot evaluate claims without quantitative research design.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-2b248fda remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-b85574e7 remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-a7e88a26 remains unresolved: no figures present in paper/source/main.tex for evaluation. Per R3 rules, this lens cannot assess figure quality when no figures exist.
- `claim_accuracy` [writing] `(unstated)` — Concern claim_accuracy-5018f2b6 remains unresolved: Tibshirani 1996 DOI '10.1111/j.2517-6161.1996.tb02080.x' still requires verification against official publication record. Reviser response indicates no changes were made due to missing tasks.md.
- `claim_accuracy` [writing] `(unstated)` — Concern claim_accuracy-c3f45551 remains unresolved: Claim 'correctly identifies the Lasso paper as a positive contribution under all of its lenses' still lacks supporting evidence. No quantitative metrics or explicit panel verdicts added. Reviser response indicates no changes were made.
- `scientific_evidence` [science] `(unstated)` — Prior concern scientific_evidence-fc71ef91 remains unresolved: paper still lacks empirical evidence (sample sizes, statistical tests, effect sizes, controls, replication). Reviser response indicates no-op due to missing tasks.md, but the scientific evidence deficit in the manuscript itself is unchanged.
- `writing_quality` [writing] `paper/source/main.tex` — Full paper LaTeX source not provided. Only synthetic seed excerpt (1 paragraph) available for review. Cannot assess overall writing quality without complete manuscript.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-0735bb03 remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-4d88b143 remains unresolved: no figures exist in this artifact to evaluate. The reviser's response indicates tasks.md is missing, preventing proper pipeline progression.
- `figure_critic` [writing] `(unstated)` — Prior concern figure_critic-1225b5f5 remains unresolved: no figures present in paper/source/main.tex for evaluation. Per R3 rules, this lens cannot assess figure quality when no figures exist.

**Adjudication** (maintainer to fill in):

- [ ] 1.1: legitimate / spurious — reasoning:
- [ ] 1.2: legitimate / spurious — reasoning:
- [ ] 1.3: legitimate / spurious — reasoning:
- [ ] 1.4: legitimate / spurious — reasoning:
- [ ] 1.5: legitimate / spurious — reasoning:
- [ ] 1.6: legitimate / spurious — reasoning:
- [ ] 1.7: legitimate / spurious — reasoning:
- [ ] 1.8: legitimate / spurious — reasoning:
- [ ] 1.9: legitimate / spurious — reasoning:
- [ ] 1.10: legitimate / spurious — reasoning:
- [ ] 1.11: legitimate / spurious — reasoning:
- [ ] 1.12: legitimate / spurious — reasoning:
- [ ] 1.13: legitimate / spurious — reasoning:
- [ ] 1.14: legitimate / spurious — reasoning:
- [ ] 1.15: legitimate / spurious — reasoning:
- [ ] 1.16: legitimate / spurious — reasoning:
- [ ] 1.17: legitimate / spurious — reasoning:
- [ ] 1.18: legitimate / spurious — reasoning:
- [ ] 1.19: legitimate / spurious — reasoning:
- [ ] 1.20: legitimate / spurious — reasoning:
- [ ] 1.21: legitimate / spurious — reasoning:
- [ ] 1.22: legitimate / spurious — reasoning:
- [ ] 1.23: legitimate / spurious — reasoning:
