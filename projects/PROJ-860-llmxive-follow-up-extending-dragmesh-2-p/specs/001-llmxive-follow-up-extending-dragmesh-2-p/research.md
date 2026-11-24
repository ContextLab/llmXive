# Research: Virtual Tactile Zero-Shot Adaptation

## Problem Statement
Static reward functions for dexterous hand manipulation (e.g., PICA) fail when the friction of a novel articulated object lies outside the training distribution. Physical tactile sensors are unavailable in many simulators. This work investigates whether a **Dynamic Resistance Proxy** (`k_norm`)—computed from torque and velocity derivatives—can supply sufficient feedback for *zero‑shot* adaptation of reward weights, enabling the policy to succeed on high‑ and low‑friction objects without prior exposure.

## Dataset Strategy

| Dataset | Purpose | Loader / URL | Verification |
|---|---|---|---|
| **DragMesh‑2** | Base geometries for generating novel articulated objects | `datasets.load_dataset("AIGeeksGroup/DragMesh-2", split="train")` or direct download ` | **Verified** (provided in the “Verified datasets” block) |

- **Availability**: Direct HTTP download; no credentials required.  
- **Variable Fit**: The manifest supplies mesh identifiers; friction coefficients are assigned programmatically during object generation (FR‑010). No other external variables are needed.  

## Methodology

### 1. Dynamic Resistance Proxy (FR‑001, FR‑006, FR‑007)
- Compute per‑timestep:  

  \[
  k_{\text{norm}} = \frac{|\Delta \tau_{\text{hand}}|}{\max(|\Delta v_{\text{object}}|,\;\epsilon)\; N}
  \]  

  with \(\epsilon = 10^{-4}\) and clamping to \([10^{-4}, 10]\).  
- Apply a **moving average filter** (window = 5) to \(|\Delta \tau_{\text{hand}}|\) before division (source: Gaussian filter, https://en.wikipedia.org/wiki/Gaussian_filter).  
- Log `N` (normal contact force) each timestep (FR‑009).

**Construct Validity Note**: While `k_norm` is influenced by object geometry and mass (through torque and velocity), normalizing by the estimated normal force `N` mitigates these confounds, making the ratio more directly reflective of surface friction. The subsequent **controlled correlation experiment** (see §4) explicitly tests this relationship.

### 2. Adaptive Reward Scheduler (FR‑002, FR‑011)
- Compute the percentile of the current `k_norm` within the **training‑distribution** proxy values (collected during baseline training).  
- If percentile > 90 % → increase detachment reward `r_detach` by **≥ 20 %**.  
- If percentile < 10 % → decrease contact reward `r_contact` by **≥ 15 %**.  

**Sensitivity Analysis**: Task T045b will evaluate alternative thresholds (80/20, 85/15) to ensure robustness; the final thresholds will be chosen based on highest improvement without destabilizing training.

### 3. Zero‑Shot Evaluation (FR‑003, FR‑010, SC‑001, SC‑002)
- **Novel Object Set**: A specific number of articulated objects, each with friction coefficient ∈ [0.8, 1.2] (high) or ≤ 0.1 (low), i.e., outside the training range [0.2, 0.6].  
- **Policies**:  
  1. **Static PICA** (baseline).  
  2. **Adaptive PICA** (uses `k_norm`).  
  3. **Ablation – Random Proxy** (random values in the same range, no signal).  

- **Metric**: Binary *success* (goal reached within time limit).  
- **Ablation Design**: Each object is evaluated under **all three policies** with identical initial conditions; only the proxy value differs, controlling for object‑specific factors (mass, geometry).

### 4. Correlation‑Validation Experiment (FR‑008, SC‑006)
- Run **≥ 30** trials where the true friction coefficient is known.  
- Record `k_norm` **and** the normal force `N`.  
- Two analysis variants:  
  1. **N‑normalized correlation**: compute Pearson r between `k_norm / N` and ground‑truth friction.  
  2. **Partial correlation**: compute Pearson r between `k_norm` and friction while controlling for `N`.  
- Pass condition: \(r ≥ 0.8\) in either variant.

### 5. Statistical Analysis (FR‑005, SC‑005)
- **GLMM**: Fit a **Generalized Linear Mixed Model** (logit link) with:  
  - Fixed effect: `policy_type` (adaptive vs static).  
  - Random intercept: `object_id`.  
  - Report **p < 0.05** for the policy effect and improvement % (target ≥ 15 %).  
- **Paired t‑test** (Constitution Principle VII): For each object, compute the difference in success (adaptive − static). Perform a paired‑t‑test across the selected objects.; report p‑value and effect size. This satisfies the mandated validation method.  

### 6. Compute Feasibility (FR‑004, SC‑003, SC‑004)
- All code runs on **CPU‑only** PyBullet (`p.connect(p.DIRECT)`).  
- No CUDA imports; `torch` installed with `+cpu`.  
- Target wall‑clock ≤ 6 h, peak RAM ≤ 7 GB on a free‑tier GitHub Actions runner.  
- If resource usage exceeds limits, the pipeline will automatically down‑sample the number of objects (up to a minimum of 10) and re‑run; power analysis (Task T045) will flag any resulting power loss.

## Decision/Rationale

| Decision | Rationale |
|---|---|
| **GLMM + Paired t‑test** | Binary outcomes demand a GLMM for mixed‑effects inference *and* a paired‑t‑test to satisfy Constitution Principle VII. Both are run; GLMM handles random effects, t‑test provides the mandated direct comparison. |
| **Ablation with Random Proxy** | Controls for object‑specific factors by evaluating all policies on the *same* objects with identical seeds; only the proxy is randomized. |
| **CPU‑only execution** | Mandated by Constitution Principle VI and SC‑003/SC‑004; enforced by Task T015d. |
| **Moving‑average window = 5** | Directly matches the verified filter size (Gaussian filter source). |
| **DragMesh‑2 as sole data source** | Open, programmatically downloadable, and provides required geometry; friction is assigned during generation, meeting dataset‑variable fit. |
| **Dynamic Resistance Proxy construct validity** | Acknowledged that torque and velocity derivatives also depend on geometry and mass; justified via the *controlled* correlation experiment that normalizes by contact force `N`. |
| **Reward thresholds** | Sensitivity analysis (Task T045b) will verify that 90th/10th percentiles are robust; alternative thresholds are explored. |
| **Power analysis** | Quick analytical check (Task T045) ensures sufficient statistical power; if under‑powered, object count is increased up to 20 while staying within the 6 h budget. |

## Risks & Mitigations

| Risk | Likely Cause | Fix |
|---|---|---|
| Simulation instability at extreme friction | Too high/low friction causing exploding forces | Clamp `k_norm` (FR‑007) and cap reward scaling; fallback to reduced timestep if PyBullet reports high forces. |
| Insufficient statistical power | Only a limited number of objects for GLMM | Power analysis (T045) will trigger increase of `--num_objects` up to 20; GLMM and paired t‑test will be re‑run. |
| Noisy derivatives | Simulation jitter | Apply mandatory moving‑average filter; if still noisy, increase window size to 7 in a secondary run (still documented). |
| Spec‑analysis mismatch | Amendment proposal replaces paired‑t‑test | Amendment adds paired‑t‑test *in addition* to GLMM; both are documented and versioned. |
| Memory overflow | Large logs or many objects | Stream CSV rows during GLMM fitting; limit episode length and use PyBullet’s `MAX_SUBSTEPS` to reduce state size. |

---


## Expected Deliverables
- **Generated objects** (`data/generated/novel_objects/*.json`).  
- **Simulation logs** (`data/logs/simulation_run_*.csv`).  
- **Correlation experiment results** (`data/logs/correlation_results.json`).  
- **Statistical analysis outputs** (`data/logs/glmm_summary.txt`, `data/logs/paired_t_test.txt`).  
- **Experiment summary** (`data/logs/experiment_summary.json`).  
- **Documentation** (`docs/README.md`, `docs/CHANGELOG.md`).  

All artifacts are checksum‑validated and referenced in the project state YAML for reproducibility.
