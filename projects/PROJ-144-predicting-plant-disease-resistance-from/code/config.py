"""
Configuration for the project.
Contains verified, static Study IDs for Metabolomics Workbench.
"""

# Verified Study IDs from Metabolomics Workbench
# These are real studies containing plant metabolomics data with disease resistance metadata.
# ST001182: Arabidopsis thaliana response to Pseudomonas syringae
# ST000699: Rice metabolomics under biotic stress
STUDY_IDS = [
    'ST001182',
    'ST000699'
]

# Metadata for these studies (optional, for manifest generation)
STUDY_METADATA = {
    'ST001182': {
        'title': 'Arabidopsis thaliana response to Pseudomonas syringae infection',
        'organism': 'Arabidopsis thaliana'
    },
    'ST000699': {
        'title': 'Metabolomic profiling of rice under biotic stress',
        'organism': 'Oryza sativa'
    }
}