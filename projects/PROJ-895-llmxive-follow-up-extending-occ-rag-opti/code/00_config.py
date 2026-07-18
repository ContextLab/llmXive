"""
Configuration module for OCC-RAG project.
"""
import os
import torch

class Config:
    def __init__(self):
        self.MODEL_ID = "canonical/occ-rag-frozen"
        self.MASK_FRACTION = 0.1
        self.RETENTION_PCT = 0.5
        self.FINE_TUNE_SAMPLE_SIZE = 100
        self.SAMPLE_SEED = 42
        self.MAX_RAM_THRESHOLD = 7.0
        self.SAMPLE_TRIGGER_SIZE = 1000
        
    def validate_config(self):
        pass

CONFIG = Config()

def validate_config():
    pass