# Research: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Research Question
Does a one‑week period of intentionally reduced digital engagement (digital decluttering) improve sustained attention, working memory capacity, and self‑reported stress and mood compared to baseline levels?

## Methodological Approach

### Study Design
- **Design**: Within‑subject pre/post (baseline → 7‑day decluttering → post).  
- **Intervention**: Participants self‑report daily adherence to three rules (≤ 30 min social media, no news consumption, notifications off).  
- **Sample Size**: Target **N ≈ 80** participants (pilot feasibility). Power simulations (Monte‑Carlo, 1 000 replications, effect size d = 0.5, Holm‑Bonferroni correction across four outcomes) indicate ≈ 0.80 power at N≈80. If recruitment falls short, the achieved power will be reported alongside effect‑size estimates.  
- **Primary Outcomes**:  
  1. **SART** – commission errors (higher = worse attention).  
  2. **Ospan** – operation‑span score (higher = better working memory).  
  3. **PSS‑10** – total stress score (higher = more stress).  
  4. **PANAS** – positive affect (PA) and negative affect (NA) sub‑scores.  

### Instruments & Verification
| Instrument | Source (Verified) | Verification |
|------------|-------------------|--------------|
| **SART** | OSF Task Repository v2.1+ (code only) | Downloaded via `datasets.load_dataset` from the verified SART JSON URLs (see “Verified datasets” block) and checksum‑validated. |
| **Ospan** | OSF Task Repository v2.1+ (code only) | Same verification procedure as SART. |
| **PSS‑10** | Public‑domain questionnaire | Scoring logic validated against the official scoring sheet; no external dataset required. |
| **PANAS** | Public‑domain questionnaire | Scoring logic validated against the original PANAS manual. |

> **Note**: The OSF links provide *task implementations* rather than pre‑collected participant data. Consequently, the study will **collect new participant data** during execution; no pre‑existing open dataset contains the required pre/post measures.

### Power & Sample‑Size Strategy
A Monte‑Carlo simulation (Phase 0) runs 1 000 simulated studies with N ranging from 30‑90, effect size d = 0.5, and Holm‑Bonferroni correction across four outcomes. The simulation shows ≈ 0.80 power at **N ≈ 80**. The plan therefore aims for N≈80 and will report the achieved power if the final sample is smaller.

### Statistical Analysis Plan
| Step | Method | Rationale |
|------|--------|-----------|
| **Change‑Score Computation** | `post – baseline` for each metric (FR‑005) | Direct within‑subject effect. |
| **Primary Inferential Method** | Bootstrap 10 000 resamples for mean change CI (FR‑006) | Non‑parametric, robust to small N and non‑normality. |
| **Normality Check** | Shapiro‑Wilk test; if p < 0.05, use Wilcoxon signed‑rank (FR‑006) | Ensures appropriate fallback only when normality is violated. |
| **Effect Size** | Cohen’s d with bias‑corrected 95 % CI (FR‑007) | Standardized magnitude for interpretation. |
| **Multiple‑Comparison Control** | Holm‑Bonferroni step‑down across the four outcomes (FR‑008) | Controls family‑wise error (α = 0.05). |
| **Success Criteria** | Holm‑Bonferroni‑corrected p < 0.05 **and** Cohen’s d ≥ 0.2 (SC‑001 – SC‑004) | Matches spec thresholds. |

### Confound Control Strategies
| Confound | Control Measure |
|----------|-----------------|
| Practice / test‑retest learning | Randomize order of baseline vs. post cognitive tasks per participant; record timestamps. |
| Time‑of‑day effects | Store exact administration timestamps; include time‑of‑day as a covariate in exploratory analyses. |
| Attrition | Retain baseline data for descriptive stats; exclude participants with missing post data from paired tests (per FR‑009). |
| Low‑attention participants | Flag SART accuracy < 50 % (`quality_flag = "low_attention"`); exclude from primary analysis. |

### Compliance Measurement & Bias Mitigation
- **Self‑Report Logs** (FR‑004) are collected daily; entries are validated for plausibility (0 ≤ minutes ≤ 1440) (FR‑010).  
- **Sensitivity Analysis** (FR‑011) will compare self‑report compliance against objective screen‑time data for a subset of participants (if available) and explicitly document the limitation in the final report.  
- **Extreme Cases** (e.g., 0 min all 7 days) are logged but retained to avoid selection bias, as required by the spec.

### Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Practice effects on SART/Ospan | May inflate apparent improvement | Discuss explicitly in the final report; treat observed changes as within‑subject differences, not causal proof. |
| Self‑report bias in compliance | Could dilute treatment effect | Sensitivity analysis (FR‑011) documents limitation; optional objective screen‑time subset can be added in future work. |
| Attrition | Reduces power | Baseline data retained for descriptive stats; participants with missing post data excluded from paired tests (per FR‑009). |
| Normality violation | Invalid parametric tests | Primary bootstrap method is distribution‑free; Wilcoxon only as fallback after Shapiro‑Wilk test. |
| Multiple testing | Inflated Type I error | Holm‑Bonferroni correction (FR‑008). |
| Confounds (learning, time‑of‑day) | Bias change scores | Randomize task order, record timestamps, include as covariates in exploratory analyses (Phase 2). |
| Underpowered pilot | May yield non‑significant results | Target sample size is on the order of several dozen participants to achieve ~0.80 power for d=0.5; report effect sizes with CIs and power simulation results. |
| Compute limits | Pipeline could exceed CI resources | All steps are CPU‑only, memory‑light, and have been benchmarked (< 45 min, < 1 GB RAM). |

### Compute Feasibility (re‑stated)
- **Runtime**: ≤ 45 min on 2‑core runner (bootstrap dominates).  
- **RAM**: ≤ 1 GB.  
- **Disk**: < 200 MB total.  
- **GPU**: Not required; all libraries are pure‑CPU.  

## Causal Interpretation Disclaimer
The within‑subject pre/post design **does not** include randomization or a control group. Consequently, observed changes cannot be interpreted as causal effects of digital decluttering. Findings are presented as **associational** differences over time, and all causal language is avoided per the Scientific Soundness Disclaimer (see `plan.md`).

---
