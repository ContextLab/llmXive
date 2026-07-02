"""
llmXive Solar Wind Correlation Project package initialization.

This module sets up the logging infrastructure as specified in T006.
"""
import logging

# Create a logger named 'solar_wind' with level 'INFO'
logger = logging.getLogger('solar_wind')
logger.setLevel(logging.INFO)

# Add a StreamHandler to the logger
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Prevent the logger from propagating to the root logger to avoid duplicate logs
logger.propagate = False