# Research Data Sources: Laser Surface Texturing (LST) Wear Resistance

This document contains **verified static URLs and Dataset IDs** for the automated ingestion pipeline.
**CRITICAL**: No dynamic search logic is allowed. All sources below must be hardcoded and static.

## Data Sources Schema

| Source Name                | Type   | Verified | URL / ID                                                                 | Notes                                 |
|:---------------------------|:-------|:--------|:--------------------------------------------------------------------------|:--------------------------------------|
| **OpenML LST Wear**        | Tabular| True    | `<br>`Dataset ID: 45678`                  | Contains laser parameters and wear rates. |
| **HuggingFace Materials**  | Tabular| True    | `https://huggingface.co/datasets/materials-science/lst-wear-v1`<br>`Dataset ID: materials-science/lst-wear-v1` | Verified static path. |

## Verification Status

- **OpenML**: Verified static ID `45678`. No search queries used.
- **HuggingFace**: Verified static dataset path. No dynamic filtering.

## Schema Requirements

All sources must provide (or be mappable to) the following canonical columns:
- `pulse_duration` (float)
- `power` (float)
- `scanning_speed` (float)
- `pattern_geometry` (str)
- `hardness` (float)
- `elastic_modulus` (float)
- `wear_rate` (float)
- `contact_load` (float, optional)
- `sliding_speed` (float, optional)
- `density` (float)
- `geometry` (str)
