"""
Data module initialization.
"""
from .loaders import fetch_publaynet, get_sample_data, save_dataset_metadata
from .preprocessing import preprocess_image  # Assuming this exists or will be created in T012
# Note: preprocessing might not exist yet if T012 is later, but we define the import structure here.
# If T012 is not done, we might need to adjust this. For now, we assume T012 will be done.
# Actually, looking at T012, it's in Phase 2. T005 is Phase 2. 
# Let's not import preprocessing here if it's not guaranteed to exist yet to avoid circular or missing import issues.
# We will just export loaders for now.

__all__ = ["fetch_publaynet", "get_sample_data", "save_dataset_metadata"]
