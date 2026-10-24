# Data Model: Mapping Cosmic Microwave Background Cold Spots to Large‑Scale Structure

The following schemas define the structure of the primary output artifacts. They are used by the contract‑validation test suite (`tests/contract/test_contracts.py`).

## 1. Cold‑Spot Candidates (`cold_spots.schema.yaml`)

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Cold Spot Candidate List"
description: "List of identified CMB cold‑spot candidates after top‑hat filtering."
type: "object"
required:
  - spots
properties:
  spots:
    type: "array"
    description: "Array of spot records; may be empty if no candidates are found."
    items:
      type: "object"
      required:
        - ra_deg
        - dec_deg
        - temperature_deviation_uK
        - sigma_level
        - filter_radius_deg
      properties:
        ra_deg:
          type: "number"
          description: "Right‑ascension in decimal degrees."
        dec_deg:
          type: "number"
          description: "Declination in decimal degrees."
        temperature_deviation_uK:
          type: "number"
          description: "CMB temperature relative to map mean (micro‑Kelvin)."
        sigma_level:
          type: "number"
          description: "Deviation in units of the map σ (negative for cold spots)."
        filter_radius_deg:
          type: "number"
          description: "Radius of the top‑hat filter applied (degrees)."
```



## 2. Cross‑Correlation Results (`correlation_results.schema.yaml`)

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Cross‑Correlation Results"
description: "Angular cross‑correlation ξ(θ) between cold spots and galaxy density for each redshift bin, plus Monte‑Carlo significance."
type: "object"
required:
  - redshift_bin
  - theta_deg
  - xi_theta
  - observed_amplitude
  - monte_carlo_pvalue
properties:
  redshift_bin:
    type: "string"
    description: "Redshift interval label, e.g., '0.2-0.4'."
  theta_deg:
    type: "array"
    description: "Angular separation bins (degrees)."
    items:
      type: "number"
  xi_theta:
    type: "array"
    description: "Cross‑correlation values corresponding to each θ."
    items:
      type: "number"
  observed_amplitude:
    type: "number"
    description: "Scalar summary of the observed ξ(θ) (e.g., integral over θ)."
  monte_carlo_pvalue:
    type: "number"
    description: "Monte‑Carlo rank‑test p‑value for the observed amplitude."
  theoretical_isw_curve:
    type: "array"
    description: "Optional: ISW theoretical ξ(θ) values for comparison."
    items:
      type: "number"
```



These schemas are deliberately minimal yet fully capture the required fields for downstream validation and reproducibility.
