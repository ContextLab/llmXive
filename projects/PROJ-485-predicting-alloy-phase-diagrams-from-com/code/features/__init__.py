"""
Features module for alloy phase diagram prediction.
Contains descriptor generation and validation logic.
"""
from .generate_descriptors import (
    load_elemental_properties,
    calculate_mean_atomic_radius,
    calculate_electronegativity_variance,
    calculate_valence_electron_count,
    calculate_hume_rothery_concentration,
    generate_descriptors,
    process_alloy_dataset,
    main
)
from .verify_elements import (
    load_csv_data,
    verify_element,
    verify_elemental_properties
)

__all__ = [
    'load_elemental_properties',
    'calculate_mean_atomic_radius',
    'calculate_electronegativity_variance',
    'calculate_valence_electron_count',
    'calculate_hume_rothery_concentration',
    'generate_descriptors',
    'process_alloy_dataset',
    'main',
    'load_csv_data',
    'verify_element',
    'verify_elemental_properties'
]
