# Idea — Sensitivity of the GW150914 chirp-mass posterior to detector-noise prior assumptions (physics)

Data source: LIGO/Virgo Open Science Center — GW150914 strain data (see also the discovery paper Abbott et al. 2016, DOI 10.1103/PhysRevLett.116.061102) (https://gw-openscience.org/); publicly accessible under an open-access policy.

Research question: For the GW150914 binary-black-hole merger detected by LIGO-Virgo, how sensitive is the inferred chirp-mass posterior to the assumed detector-noise prior model (Welch PSD vs. parametric Gaussian-process model vs. the official LIGO/Virgo PSD)?

Hypothesis: Posterior chirp-mass medians differ by <2% across the three noise models; 90% credible intervals widen by 15-25% under the parametric GP model relative to the official PSD.

Methods: Pull LIGO/Virgo GW150914 strain data from the GW Open Science Center; implement matched-filter chirp-mass inference under each PSD model; compare posterior moments + KL divergence between posteriors.

Feasibility: implementable with free open-source tooling + the publicly-accessible dataset cited above.
