# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    USER_RECORD ||--|{ GENRE_PREFERENCE : "has"
    USER_RECORD {
        string user_id (hashed)
        float openness_score
        float conscientiousness_score
        float extraversion_score
        float agreeableness_score
        float neuroticism_score
        int age
        string gender
        string country_region
    }
    GENRE_PREFERENCE {
        string user_id (hashed)
        string genre_name
        float listening_minutes
        float genre_score (normalized)
    }
    ANALYSIS_RESULT {
        string trait
        string genre
        float correlation_rho
        float p_value
        float adjusted_p_value
        boolean is_significant
        float effect_size_rho
        float ci_lower_rho
        float ci_upper_rho
        float effect_size_r_log
        float fisher_z_log
        float ci_lower_r_log
        float ci_upper_r_log
        float beta_baseline
        float beta_full
        float delta
        float cohens_d
        float vif
    }
```

## 2. Data Dictionary

### 2.1 Raw Data (Incoming)
*   **BFI-2 Source**: Expected columns: `user_id`, `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`.
*   **Last.fm Source**: Expected columns: `user_id`, `artist`, `genre`, `minutes_listened`.

### 2.2 Processed Data (`data/processed/merged_data.csv`)
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `user_id` | string | Hashed user identifier | Unique, non-null |
| `openness` | float | BFI-2 Openness score | [1.0, 5.0] |
| `conscientiousness` | float | BFI-2 Conscientiousness score | [1.0, 5.0] |
| `extraversion` | float | BFI-2 Extraversion score | [1.0, 5.0] |
| `agreeableness` | float | BFI-2 Agreeableness score | [1.0, 5.0] |
| `neuroticism` | float | BFI-2 Neuroticism score | [1.0, 5.0] |
| `age` | int | Age in years | > 0 |
| `gender` | string | Categorical | {Male, Female, Other, Unknown} |
| `country_region` | string | Grouped country | {North America, Europe, Asia, South America, Africa, Oceania, Other} |
| `genre` | string | Standardized genre | {Rock, Pop, Hip-Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other} |
| `minutes_listened` | float | Log-transformed minutes | >= 0 |

### 2.3 Analysis Results (`data/processed/analysis_results.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `trait` | string | One of the 5 Big Five traits |
| `genre` | string | One of the 10 standardized genres |
| `correlation_rho` | float | Spearman correlation coefficient |
| `p_value` | float | Raw p-value |
| `adjusted_p_value` | float | Benjamini-Hochberg corrected p-value |
| `is_significant` | boolean | True if `adjusted_p_value` < 0.05 |
| `effect_size_rho` | float | Spearman's rho (primary effect size) |
| `ci_lower_rho` | float | 95% CI lower bound (bootstrapped) |
| `ci_upper_rho` | float | 95% CI upper bound (bootstrapped) |
| `effect_size_r_log` | float | Pearson's r on log-transformed data (secondary) |
| `fisher_z_log` | float | Fisher's z for log-data (secondary) |
| `ci_lower_r_log` | float | 95% CI lower bound for log-data (secondary) |
| `ci_upper_r_log` | float | 95% CI upper bound for log-data (secondary) |
| `beta_baseline` | float | Beta coefficient from baseline model (Trait only) |
| `beta_full` | float | Beta coefficient from full model (Trait + Covariates) |
| `delta` | float | Change in beta (beta_full - beta_baseline) |
| `cohens_d` | float | Cohen's d for the coefficient delta |
| `vif` | float | Variance Inflation Factor |

## 3. Transformation Logic

1.  **Genre Standardization**:
    *   Input: Raw tag (e.g., "alt", "rock", "alternative rock").
    *   Logic: Lookup table mapping. If no match, assign "Other".
    *   Output: One of the 10 standard genres.
2.  **Demographic Grouping**:
    *   Input: Country code (e.g., "US", "GB", "DE").
    *   Logic: Map to continent/region. If country is rare (< 1% of sample), assign "Other".
    *   Output: Region string.
3.  **Log Transformation**:
    *   Input: `minutes_listened` (raw).
    *   Logic: `log(minutes + 1)` to handle zeros and skew.
    *   Output: `minutes_listened` (transformed).
4.  **Coefficient Delta**:
    *   Input: Regression results from baseline and full models.
    *   Logic: Calculate $\Delta\beta = \beta_{full} - \beta_{baseline}$ and Cohen's $d$.
    *   Output: `delta`, `cohens_d`.