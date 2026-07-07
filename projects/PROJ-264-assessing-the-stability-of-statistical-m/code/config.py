"""
Project configuration constants.
Defines the fixed set of 15 binary classification dataset IDs (OpenML)
as required by Constitution Principle VII.
"""

# Explicit list of 15 binary classification dataset IDs from OpenML
DATASET_IDS = [
    2,    # Australian
    14,   # German Credit
    31,   # Hepatitis
    37,   # Pima Indians Diabetes
    42,   # Breast Cancer Wisconsin (Original)
    159,  # Heart Disease (Cleveland)
    451,  # Sonar
    633,  # Ionosphere
    1464, # Banknote Authentication
    1494, # Blood Transfusion
    1501, # Haberman's Survival
    1510, # Breast Cancer Wisconsin (Diagnostic)
    1590, # Credit Approval (UCC)
    1822, # Tic-Tac-Toe Endgame (Binary target)
    1898, # Phishing Websites
]

# Base URL for UCI direct fetch if OpenML fails
UCI_BASE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases"

# Checksum cache file path relative to project root
CHECKSUM_CACHE_PATH = "data/raw/checksums.json"
