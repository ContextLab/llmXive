"""
Custom exception definitions for the Brain Dynamics and Creativity pipeline.
"""

class DataMissingCreativityError(Exception):
    """
    Raised when the Creative Achievement Questionnaire (CAQ) field is missing
    or null in the behavioral metadata for a participant.
    """
    pass
