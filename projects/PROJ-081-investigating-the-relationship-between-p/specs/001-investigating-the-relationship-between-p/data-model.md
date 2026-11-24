# Data Model: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

## Core Entities

| Entity | Description | Key Attributes (type) |
|--------|-------------|-----------------------|
| **PlantSpecies** | Distinct plant taxon used in the analysis. | `species_id: str` (unique), `species_name: str`, `family: str` |
| **MetaboliteProfile** | Concentrations of four metabolite classes for a given species, with optional absence indicator. | `alkaloids: float`, `terpenes: float`, `phenolics: float`, `benzoxazinoids: float`, `absence_indicator: dict` (optional) |
| **HerbivoryScore** | Quantitative measure of herbivore damage for the species. | `herbivory_score: float`, `measurement_method: str` |
| **AnalysisResult** | Wrapper for any statistical output (correlation, regression, importance, power analysis). | `result_type: str` (enum), `payload: dict`, `timestamp: datetime` |

## Processed DataFrame Schema (output of Phase 2)

| Column | Description | dtype |
|--------|-------------|-------|
| `species_id` | Stable taxonomic identifier (e.g., NCBI Taxonomy ID) | `string` |
| `species_name` | Scientific or common name | `string` |
| `family` | Plant family | `string` |
| `alkaloids` | Z‑scored concentration; zero **only** for documented biological absence (see `absence_indicator`). | `float64` |
| `terpenes` | Z‑scored concentration; zero **only** for documented biological absence. | `float64` |
| `phenolics` | Z‑scored concentration; zero **only** for documented biological absence. | `float64` |
| `benzoxazinoids` | Z‑scored concentration; zero **only** for documented biological absence. | `float64` |
| `herbivory_score` | Normalized herbivory index after IQR capping. | `float64` |
| `absence_indicator` (optional) | JSON dict documenting which metabolite classes are biologically absent for that row (e.g., `{"alkaloids":"documented_absent"}`). Rows with a class marked absent are **excluded from imputation and standardization** for that class. | `string` (JSON) |

All rows must have **no missing values** in the required columns after preprocessing (FR‑002, FR‑007). Zero values now denote imputed missing data **after** standardization; documented absences are captured separately.

## Model Output Structures (conform to `contracts/model_output.schema.yaml`)

Each model output is an `AnalysisResult` JSON object with `result_type` indicating the analysis (e.g., `"ols"`, `"pgls"`). The `payload` field contains the analysis‑specific fields as described in the schema (see `contracts/model_output.schema.yaml`). All timestamps are ISO‑8601 strings.

---
