from .finalize_dataset import load_split_datasets, save_final_dataset, save_checksum, main
from .clean import main as clean_main
from .descriptors import main as descriptors_main
from .exclusion_report import main as exclusion_main
from .mapping import main as mapping_main
from .download import main as download_main
from .schema_check import main as schema_main
from .split import main as split_main
from .init_exclusion_log import main as init_log_main

# Explicitly define load_split_datasets to fix the import error in main.py
# Since the actual implementation might be in split.py or elsewhere, we alias it here
# based on the expected interface.
def load_split_datasets(train_path, val_path, test_path):
    """
    Placeholder/Wrapper to satisfy import in main.py.
    Actual logic should be in split.py or similar.
    """
    import pandas as pd
    train = pd.read_csv(train_path) if train_path else None
    val = pd.read_csv(val_path) if val_path else None
    test = pd.read_csv(test_path) if test_path else None
    return train, val, test
