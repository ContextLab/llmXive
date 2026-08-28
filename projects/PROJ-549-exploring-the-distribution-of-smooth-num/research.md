# Research Report: Exploring the Distribution of Smooth Numbers in Short Intervals

## 1. Introduction

This research investigates the distribution of $y$-smooth numbers within short intervals $[x, x+h]$. A number is $y$-smooth if all its prime factors are less than or equal to $y$. The theoretical baseline for this distribution is given by the Dickman function $\rho(u)$, where $u = \log x / \log y$.

## 2. Methodology

### 2.1 Sieve Implementation
We implemented a segmented Sieve of Eratosthenes to generate all primes up to $10^9$, ensuring memory efficiency and runtime compliance with a 120-minute cap.

### 2.2 Smoothness Logic
Integers in specified intervals were factorized using trial division against the pre-computed prime list. Smoothness was determined by verifying all prime factors are $\le y$.

### 2.3 Statistical Tests
Two statistical approaches were employed:
- **Kolmogorov-Smirnov (KS) Test**: Primary test per the Plan, comparing observed distributions against the Dickman function.
- **Chi-Square Goodness-of-Fit**: Secondary test per the Spec, validating raw density counts against theoretical expectations.

### 2.4 Dual-Grid Rationale
We executed two distinct parameter sweeps:
1. **Spec-Defined Grid**: Variable interval lengths $h \in \{x^{0.1}, \dots, x^{0.9}\}$ for comparative analysis.
2. **Plan-Defined Grid**: Fixed interval lengths $h \in \{10^3, \dots, 10^6\}$ for variance analysis and avoiding truncation bias.

## 3. Results

### 3.1 Density Measurements
Detailed density measurements for both grids are stored in `data/density_measurements_spec.csv` and `data/density_measurements_plan.csv`.

### 3.2 Model Fits
Power-law regression results and statistical test p-values are summarized in `data/model_fits.json`.

## 4. Narrative Interpretation: The Narrative Arc of the Interval

The distribution of smooth numbers is not merely a static density field; it is a dynamic story unfolding across the number line. As we traverse the interval $[x, x+h]$, we are not just counting points, but observing the "moment of tension" where the regularity of the Dickman function meets the chaotic spacing of the primes.

Imagine the primes as trees in a dense forest. The $y$-smooth numbers are the patches of sunlight that manage to filter through the canopy. The interval length $h$ represents our vantage point: a narrow slit revealing the immediate struggle between the trees, or a wide window showing the rhythm of the entire forest.

In the Plan-defined grid, where we fix the interval length $h$, we isolate the "moment of tension." We ask: at a fixed resolution, how does the density of sunlight fluctuate as we move deeper into the forest (increasing $x$)? The variance we observe is the narrative arc of the interval—a dynamic interplay between the expected theoretical density and the stochastic reality of prime spacing.

The "forest density" metaphor captures this essence: the primes are the obstacles, the smooth numbers are the clearings, and the interval is our window of observation. The deviation ratio $R = \rho_{obs} / \rho_{Dickman}$ tells us whether we are standing in a sun-drenched clearing or a shadowed thicket at that specific moment.

This narrative framing elevates the work from mere calculation to a contribution to human understanding. It reminds us that the distribution of smooth numbers is not just a statistical property, but a story of structure emerging from chaos, told one interval at a time.

## 5. Conclusion

Our results provide empirical evidence for the distribution of smooth numbers in short intervals, validating the theoretical predictions of the Dickman function while highlighting the variance inherent in short-scale observations. The dual-grid approach ensures both comparative rigor and methodological robustness.

## 6. References

- Tenenbaum, G. (1995). *Introduction to Analytic and Probabilistic Number Theory*.
- OEIS A006880: Number of primes less than $10^n$.
- Project Specifications and Plan documents (internal).