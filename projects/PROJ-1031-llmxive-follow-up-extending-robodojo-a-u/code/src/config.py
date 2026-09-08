# code/src/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_HF_ID = "RoboDojo/RoboDojo-v1"
DATASET_COMMIT_HASH = "v.1"
REAL_WORLD_SPLIT = "real_world"
SEED = 42
RAM_LIMIT_GB = 6
PLANNING_TIMEOUT_S = 60
POSE_DEV_TOLERANCE_CM = 5.0
ORIENT_DEV_TOLERANCE_DEG = 15.0
