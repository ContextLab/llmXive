# Research Decisions: Long-Context VLM Validation

## Decision 1: Target Venue & Style

**Decision**: The paper will target the **arXiv** preprint server with the **`arxiv-style`** LaTeX class.
**Rationale**: The primary goal is rapid dissemination of a reproduction study with a focus on negative or inconclusive results (if applicable) and rigorous methodological transparency. arXiv allows for the immediate publication of "failed" reproductions or "inconclusive" scaling laws without the gatekeeping of a conference deadline, which is critical for the "Negative Results" claim (Claim 5).
**Alternative Rejected**: Submitting to a top-tier conference (e.g., NeurIPS, ICML) was rejected because the sample size (n=10) and CPU-only constraints make the statistical power insufficient for a standard "contribution" paper, likely leading to immediate rejection on methodological grounds.

## Decision 2: Figure Generation Toolkit

**Decision**: **Matplotlib** (v3.9.0) combined with **Seaborn** (v0.13.0) for all visualizations.
**Rationale**:
1. **Reproducibility**: These libraries are standard in the Python data science ecosystem and do not require external binary dependencies (unlike Plotly's web-based rendering).
2. **Static Output**: The paper requires static PDF figures for the LaTeX build. Matplotlib/Seaborn generate high-resolution vector PDFs natively.
3. **Contract Compliance**: The `figure-data.schema.yaml` requires static data binding; Matplotlib's API is deterministic and scriptable, ensuring the "Figure Generation Agent" can regenerate exact plots from `results/` JSON files.
**Alternative Rejected**: Plotly was rejected because its default output is HTML/JS, which complicates the static PDF compilation process required by the LaTeX Build Gate.

## Decision 3: Citation Manager & Reference Style

**Decision**: **BibTeX** with the **`plain`** style (or `unsrt` if chronological ordering is preferred for the timeline of claims).
**Rationale**:
1. **Standard Compliance**: BibTeX is the de facto standard for computer science papers, especially those targeting arXiv.
2. **Verification**: The Reference-Validator Agent can easily parse `.bib` files to verify `verification_status` against the `bibliography.schema.yaml`.
3. **Constraint**: No new citations are introduced at this stage; the bibliography is strictly limited to the validated URLs from the research stage (Original Paper, MMLongBench, Qwen Model).
**Alternative Rejected**: `biblatex` was rejected to minimize build complexity and potential conflicts with the `arxiv-style` template, which is optimized for standard BibTeX.

## Decision 4: Statistical Approach for Scaling Trends

**Decision**: **Descriptive Linear Regression** (Ordinary Least Squares) with explicit **R² reporting** and **Trend Classification**.
**Rationale**:
1. **Sample Size**: With n=10, the power to detect significant effects is low. Claiming statistical significance (p < 0.05) would be scientifically dishonest (Constitution Principle IV).
2. **Transparency**: Reporting the slope coefficient and R² allows readers to judge the strength of the trend themselves.
3. **Failure Mode**: If R² < 0.1, the trend is classified as "inconclusive" or "highly variable" (Claim 3), preventing over-interpretation of noise.
**Alternative Rejected**: Bootstrapping or Bayesian inference was rejected as they add unnecessary complexity for a descriptive study where the primary goal is to check for *catastrophic* degradation (Claim 2) rather than precise parameter estimation.

## Decision 5: Hardware Constraint Enforcement

**Decision**: **4-bit Quantization (NF4)** via `bitsandbytes` is mandatory.
**Rationale**:
1. **Memory**: `Qwen2.5-VL-7B` in FP16 requires ~14GB RAM. Low-bit quantization reduces this to a size fitting the 7GB constraint.
2. **Reproducibility**: This is a hard constraint for the "CPU-only" scenario. Without it, the experiment fails immediately (Claim 5).
3. **Trade-off**: The paper must explicitly discuss the potential impact of quantization noise on the deviation metric (Claim 1).
**Alternative Rejected**: Running on a GPU (if available) was rejected because the paper's specific claim is about the feasibility of evaluation on *standard* hardware (CPU), and the "Resource Feasibility" claim (Claim 4) depends on this constraint.
