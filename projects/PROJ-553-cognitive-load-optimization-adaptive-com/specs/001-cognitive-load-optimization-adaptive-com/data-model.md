# Data Model: Cognitive Load Optimization

## 1. Entities & Relationships

### Session
Represents a learner's interaction history.
- **Attributes**: `session_id` (UUID), `user_id` (anonymized), `start_time`, `end_time`, `total_interactions`.
- **Derived**: `estimated_load` (float, 0-100), `complexity_tier` (enum: simple, moderate, complex).

### Interaction
Individual event within a session.
- **Attributes**: `interaction_id`, `session_id`, `timestamp`, `response_time_ms`, `is_correct` (bool), `hint_requested` (bool), `item_id`.

### GoldenSetLabel
**External** expert label for validation.
- **Attributes**: `interaction_id`, `expert_load_score` (float, 0-100), `labeler_id` (expert ID).
- **Constraint**: MUST be manually curated or from a verified dataset with concurrent self-reports. **NO synthetic generation.**

### ComplexityTier
Generated instructional text.
- **Attributes**: `tier_id`, `source_item_id`, `tier_level` (simple/mod/complex), `text_content`, `flesch_kincaid_grade`, `sentence_count`, `jargon_density`.

### SimulationResult
Outcome of the adaptive/static simulation.
- **Attributes**: `session_id`, `condition` (adaptive/static), `estimated_efficiency`, `load_score`, `tier_selected`.

## 2. Data Flow

1. **Raw Data** (CSV/JSON) $\to$ **Processed Interactions** (Pandas DataFrame).
2. **Processed Interactions** + **External Golden Set** $\to$ **Load Model** (Trained Regressor).
   - *Note*: The Golden Set is an external input, not derived from interactions.
3. **Instructional Text** $\to$ **Complexity Tiers** (Text + Metadata).
4. **Load Model** + **Tiers** + **Interactions** $\to$ **Simulation Results**.
5. **Simulation Results** $\to$ **Statistical Report** (Mixed-Effects Model).

## 3. Storage Schema

All data stored as CSV or JSON under `data/`.
- `data/raw/`: Original downloads (checksummed).
- `data/processed/interactions.csv`: Cleaned, feature-engineered interaction logs.
- `data/processed/golden_set.csv`: **External** validation labels (manual or verified self-reports).
- `data/explanation_tiers/`: Directory of JSON files per tier.
- `data/simulation_results/`: CSV of efficiency metrics.

## 4. Constraints

- **PII**: No raw user names or emails. `user_id` must be hashed.
- **Immutability**: Raw data files never modified. Derivations create new files.
- **Size**: Total dataset size $\le$ a manageable threshold for standard single-node processing.
- **Golden Set Integrity**: The `golden_set.csv` file MUST contain `expert_load_score` populated by human experts or verified self-reports. **Synthetic generation is forbidden.**