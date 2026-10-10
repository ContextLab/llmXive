# Research: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Decision/Rationale

- **CPU-first**: every method (Bandit, Semgrep, statsmodels GLM, scipy, matplotlib) runs natively on the 2-CPU/7 GB runner. No GPU escape hatch needed; no GPU-dependent computation is planned.
- **Statistical approach**: vulnerability counts are over-dispersed count data → Negative Binomial GLM with log(LOC) offset is the standard primary test; Mann-Whitney U on densities is the non-parametric robustness check (per FR-004). Two tests → Benjamini-Hochberg correction (FR-006). The study is observational; all claims are associational (spec assumption).
- **Tooling**: Bandit (pip-installable, CPU, Python) and Semgrep (pip-installable CLI, CPU, multi-language) satisfy the "lightweight static analysis on CPU" requirement. SonarQube Community Edition requires a Java server process and is not installable/runnable unattended within runner constraints — flagged for constitution amendment; the pipeline runs Bandit + Semgrep and documents the limitation.

## Dataset Strategy

| Dataset | Role | Verified source |
|---|---|---|
| CodeVulnBench | LLM-generated + benchmark code samples | **NO verified source found** — must not be cited with a URL. The pipeline attempts acquisition at runtime via a manifest; if unreachable, the run fails loudly with a documented data-availability error. The spec must be amended to name a verifiable open source before execution can produce real results. |
| Human-written code subset (e.g., Juliet Test Suite) | Human-written comparison group | **NO verified source found** — same handling as above; no URL fabricated. |
| SonarQube | Static analysis tool | **NO verified source found** — tool not planned for execution (see Decision/Rationale). |
| CWE taxonomy | CWE-class labeling of findings | **NO verified source found** — CWE IDs are taken directly from Bandit/Semgrep output tags; no external CWE URL is cited. |

The only verified dataset in the planning block (MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score parquet, https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet) contains text-overlap CPU scores, not code files or vulnerability annotations — it does **not** contain the variables this study needs (code files, LOC, code source group) and is therefore not used. No substitute open dataset for the LLM-vs-human code comparison exists among the verified sources.

## Statistical rigor notes

- **Multiple comparisons**: BH correction across the 2 tests (FR-006); adjusted α reported (SC-002).
- **Power**: dataset sizes are deferred; the plan acknowledges the power limitation explicitly in `results/limitations.md` and follows the spec's n ≥ 30 fallback (descriptive statistics only if violated).
- **Causal framing**: observational comparison of two code corpora; associational language only.
- **Measurement validity**: Bandit and Semgrep are widely used static analyzers; their precision/recall on this data is established empirically via the stratified human audit (FR-007/FR-008, SC-006/SC-007) rather than assumed.
- **Collinearity**: single group predictor; LOC enters as an exposure offset, not a competing predictor — no collinearity concern.

## Method summary

1. Ingest corpora → checksummed manifest (Constitution III).
2. Per-file Bandit + Semgrep → `VulnerabilityRecord` rows with CWE IDs (Constitution VII).
3. Density = findings / LOC (non-comment, non-blank); zero-LOC → `undefined`.
4. NB GLM (count ~ group, offset log LOC) + MW-U; BH correction.
5. Stratified audit sample → precision/recall/FPR by group.
6. Boxplot + CWE-class bar chart; all tables/figures machine-written to `results/`.
