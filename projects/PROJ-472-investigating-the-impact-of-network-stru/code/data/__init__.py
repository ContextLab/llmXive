"""
Data package for the llmXive research pipeline.

This package contains modules for data acquisition, preprocessing,
simulation, quality control, and storage.
"""
from .models import (
    Participant,
    StructuralConnectome,
    AvalancheRecord
)

from .download import (
    download_dMRI_data,
    run_download_pipeline,
    main
)

from .preprocess_dMRI import (
    download_parcellation,
    load_tractography,
    generate_connectome_matrix,
    save_connectome_matrix,
    run_preprocessing_for_subject,
    run_pipeline,
    main
)

from .simulate_EEG import (
    WilsonCowanSimulator,
    load_connectome,
    simulate_eeg_for_subject,
    main
)

from .quality_control import (
    calculate_snr,
    check_graph_connectivity,
    run_qc_for_subject,
    generate_qc_report,
    calculate_pipeline_completeness,
    main
)

from .store import (
    load_connectome_matrix,
    load_eeg_time_series,
    store_structural_connectome,
    store_cleaned_eeg,
    run_store_pipeline,
    main
)

__all__ = [
    # Models
    'Participant',
    'StructuralConnectome',
    'AvalancheRecord',
    
    # Download
    'download_dMRI_data',
    'run_download_pipeline',
    'main',
    
    # Preprocessing
    'download_parcellation',
    'load_tractography',
    'generate_connectome_matrix',
    'save_connectome_matrix',
    'run_preprocessing_for_subject',
    'run_pipeline',
    'main',
    
    # Simulation
    'WilsonCowanSimulator',
    'load_connectome',
    'simulate_eeg_for_subject',
    'main',
    
    # Quality Control
    'calculate_snr',
    'check_graph_connectivity',
    'run_qc_for_subject',
    'generate_qc_report',
    'calculate_pipeline_completeness',
    'main',
    
    # Storage
    'load_connectome_matrix',
    'load_eeg_time_series',
    'store_structural_connectome',
    'store_cleaned_eeg',
    'run_store_pipeline',
    'main'
]