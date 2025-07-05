#!/usr/bin/env python3
"""Test the production pipeline orchestrator integration"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline_orchestrator import ProductionPipelineOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pipeline_orchestrator():
    """Test basic pipeline orchestrator functionality"""
    logger.info("Testing production pipeline orchestrator...")
    
    try:
        # Create orchestrator (will use mock GitHub if no token)
        orchestrator = ProductionPipelineOrchestrator(
            model_size_gb=1.0,  # Small size for testing
            specific_model="microsoft/Phi-3.5-mini-instruct"  # Small test model
        )
        
        # Test project selection
        logger.info("Testing project selection...")
        project = orchestrator._select_project()
        
        if project:
            logger.info(f"Selected project: {project['id']} (stage: {project['stage']})")
            
            # Test task generation
            logger.info("Testing task generation...")
            tasks = orchestrator._generate_task_queue(project, max_tasks=3)
            
            logger.info(f"Generated {len(tasks)} tasks:")
            for i, task in enumerate(tasks):
                logger.info(f"  {i+1}. {task['type']}")
                
        else:
            logger.info("No projects available for testing")
            
        logger.info("✅ Pipeline orchestrator test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline orchestrator test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_pipeline_orchestrator()
    sys.exit(0 if success else 1)