"""
Data Synthesis Module for llmXive.
"""
from src.data_synthesis.generator import generate_activity_sequence, generate_video_stream, main
from src.data_synthesis.models import SyntheticVideoFrame, InternalStateVector, SchedulerDecision
from src.data_synthesis.handoff import ChunkManifest, HandoffManager, get_handoff_manager
from src.data_synthesis.verify_volume import load_manifest, calculate_total_duration, verify_volume, main as verify_main
from src.data_synthesis.visual_labeler import FrameLabel, VisualLabeler, main as labeler_main

__all__ = [
    'generate_activity_sequence',
    'generate_video_stream',
    'SyntheticVideoFrame',
    'InternalStateVector',
    'SchedulerDecision',
    'ChunkManifest',
    'HandoffManager',
    'get_handoff_manager',
    'load_manifest',
    'calculate_total_duration',
    'verify_volume',
    'verify_main',
    'FrameLabel',
    'VisualLabeler',
    'labeler_main'
]