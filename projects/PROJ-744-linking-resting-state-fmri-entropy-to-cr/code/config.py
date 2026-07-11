import os
from pathlib import Path

class Config:
    def __init__(self):
        # Paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DATA_RAW_DIR = self.PROJECT_ROOT / "data" / "raw"
        self.DATA_PROCESSED_DIR = self.PROJECT_ROOT / "data" / "processed"
        self.DATA_LOGS_DIR = self.PROJECT_ROOT / "data" / "logs"
        self.PHENOTYPE_PATH = self.PROJECT_ROOT / "data" / "raw" / "Creative_Problem_Solving.csv"
        
        # Entropy parameters
        self.M = 2
        self.R_FACTOR = 0.2  # r = 0.2 * SD
        self.SCALE_RANGE = (1, 20)
        
        # Motion thresholds
        self.FD_THRESHOLD = 0.2  # mm
        self.MIN_FRAMES = 100

CONFIG = Config()
