"""
Models package for llmXive RF pipeline.

Exports:
    - RFEncoder: Frozen representation forcing encoder
    - create_rf_encoder: Factory function for RFEncoder
"""
from models.rf_encoder import RFEncoder, create_rf_encoder

__all__ = ['RFEncoder', 'create_rf_encoder']