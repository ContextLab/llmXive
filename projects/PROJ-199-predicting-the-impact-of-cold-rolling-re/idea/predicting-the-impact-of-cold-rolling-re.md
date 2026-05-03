---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals  

**Field**: materials science  

## Research question  

How does the magnitude of cold‑rolling reduction quantitatively affect the crystallographic texture (pole figures, orientation distribution functions) of common face‑centered cubic metals such as aluminum, copper, and nickel?  

## Motivation  

Cold‑rolled FCC metals develop strong rolling textures that dominate yield anisotropy, formability, and fatigue life. Existing studies report texture evolution for specific alloys or processing routes, but a systematic, cross‑material mapping from reduction percentage to texture descriptors is missing. Providing a predictive relationship would enable rapid process‑design decisions without costly trial‑and‑error experiments.  

## Related work  

- [Evolution of texture and microstructure during accumulative roll bonding of aluminum AA5086 alloy (2017)](http://arxiv.org/abs/1704.06732v1) — Demonstrates pole‑figure and ODF analysis for heavily rolled aluminum, showing how multiple passes (i.e., cumulative reduction) modify texture components; useful as a methodological reference for extracting quantitative texture metrics from EBSD data.  

## Expected results  

* A set of calibrated texture descriptors (e.g., texture index, volume fractions of Brass, Copper, S, Goss components) for each metal as a continuous function of cold‑rolling reduction (0 % – 80 %).  
* A parsimonious regression or Gaussian‑process model that predicts these descriptors from reduction level with R² ≥ 0.85 on held‑out data.  
* Validation that the model reproduces known texture trends (e.g., increasing Brass component with higher reduction in Al) and generalises across the three FCC metals.  

## Methodology sketch  

1. **Data acquisition**  
   * Download publicly available EBSD datasets for Al, Cu, and Ni from the *Materials Project* (via the MP API) and the *MTData* repository (URL patterns supplied in the code).  
   * For each metal, select specimens spanning a range of cold‑rolling reductions (≈ 0 %, 20 %, 40 %, 60 %, 80 %).  
2. **Pre‑processing**  
   * Use the Python package **orix** to read .ctf/.ang files, filter out low‑quality points (confidence index < 0.1), and re‑index orientations to the FCC crystal symmetry.  
   * Convert orientations to Rodrigues vectors for downstream analysis.  
3. **Texture quantification**  
   * Compute pole figures ( {111}, {200}, {220} ) and orientation distribution functions (ODFs) with *orix*’s `OrientationDistributionFunction` class.  
   * Extract scalar texture metrics: texture index, volume fraction of the Brass ( {110}<112> ), Copper ( {112}<111> ), S ( {123}<634> ), and Goss ( {110}<001> ) components using the standard MTEX‑style component‑search algorithm implemented in **orix**.  
4. **Statistical modelling**  
   * Assemble a tidy dataset: rows = (material, reduction %). Columns = texture metrics.  
   * Fit separate regression models per material (e.g., polynomial regression up to degree 3) and a joint Gaussian‑process regression with material type as a categorical kernel.  
   * Perform 5‑fold cross‑validation; record RMSE and R² for each metric.  
5. **Model validation & visualization**  
   * Plot predicted vs. measured texture indices and component fractions across reductions.  
   * Generate contour plots of ODF sections for selected reductions to illustrate qualitative agreement.  
6. **Reproducibility packaging**  
   * All scripts (Python 3.11, `requirements.txt`) and a `Makefile` that downloads the raw EBSD files, runs the analysis, and produces a PDF report will be committed to the repository.  
   * The entire pipeline is designed to complete on a GitHub Actions runner (2 CPU, ≤ 6 GB RAM, ≤ 6 h).  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(no comparable entry found in the current corpus)*.  
- Verdict: **NOT a duplicate**.
