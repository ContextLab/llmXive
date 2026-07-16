# Data Model

## Entities

### Experiment
- experiment_id: str (unique identifier)
- source: str (Materials Project, NIST, arXiv)
- material_type: str (categorical)
- milling_speed: float (RPM)
- milling_time: float (hours)
- ball_to_powder_ratio: float
- Young's modulus: float (GPa)
- density: float (g/cm³)
- process_duration: float (hours, derived)
- D10: float (µm, target)
- D50: float (µm, target)
- D90: float (µm, target)
- raw_text_logs: str (optional)
- unstructured_flag: bool (if PSD data is image-based)

## Relationships
- One Experiment can have multiple raw data entries (from different sources)
- One Experiment maps to one processed record after merging and validation

## Constraints
- experiment_id must be unique
- D10, D50, D90 must be non-null in final dataset
- material_type must be one of the predefined categories
- process_duration derived from timestamps or text logs if missing
