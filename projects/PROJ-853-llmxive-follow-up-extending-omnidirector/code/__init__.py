"""
llmXive: Automated Science Pipeline for OmniDirector Analysis
"""
import logging
import sys

# Basic logging setup if not already configured
if not logging.getLogger().handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

__version__ = "0.1.0"
