# Configuration for llmXive project
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Graph Construction Parameters
GRANULARITY = "coarse"  # Options: "coarse", "fine"
PREDICATE_SET = "spatial"  # Options: "spatial", "spatial+temporal"

# Model Configuration
# Using a frozen VLM for discretization as per T012
MODEL_ID = "google/vit-base-patch16-224"
MAX_TRACES = 500

# Paths
DATA_DIR = "data"
RESULTS_DIR = "data/results"
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
