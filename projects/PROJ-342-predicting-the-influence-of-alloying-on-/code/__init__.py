"""
llmXive research pipeline for predicting the influence of alloying on the glass transition temperature of metallic glasses.
"""

__version__ = "0.1.0"

import logging

# Configure default logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
