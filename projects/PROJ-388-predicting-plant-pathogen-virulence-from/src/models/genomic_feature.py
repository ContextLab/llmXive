from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GenomicFeature:
    """
    Represents a specific genomic feature extracted from a pathogen isolate.

    Fields:
        feature_id: Unique identifier for this specific feature instance (e.g., 'strain123_virulence_gene_A').
        type: The category of the feature (e.g., 'virulence_gene', 'transcription_factor_site', 'secondary_metabolite_cluster').
        presence_binary: Boolean indicating presence (True) or absence (False) of the feature in the genome.
        pwm_count: Integer count of occurrences (used for PWM sites); 0 if binary presence is False.
        source: The database or method used to identify this feature (e.g., 'PHI-base', 'Pfam', 'custom_PWM').
    """
    feature_id: str
    type: str
    presence_binary: bool
    pwm_count: int
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)