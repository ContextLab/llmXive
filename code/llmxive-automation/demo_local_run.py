#!/usr/bin/env python3
"""Demo script showing llmXive automation running locally with larger models"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.response_parser import ResponseParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def demo_local_execution():
    """Demonstrate the llmXive automation system running locally"""
    
    print("=" * 80)
    print("llmXive Automation - Local Execution Demo")
    print("=" * 80)
    print()
    
    # 1. Initialize with larger model size limit
    print("1. Initializing model manager with 20GB limit (local execution)...")
    model_mgr = ModelManager(max_size_gb=20)
    
    # 2. Load a model
    print("2. Loading model from HuggingFace...")
    model, tokenizer = model_mgr.get_suitable_model()
    print(f"   ✓ Loaded: {model.name_or_path}")
    print()
    
    # 3. Initialize conversation manager
    conv_mgr = ConversationManager(model, tokenizer)
    parser = ResponseParser()
    
    # 4. Demonstrate various task types
    print("3. Executing llmXive automation tasks:")
    print("-" * 80)
    
    # Task 1: Brainstorm a new idea
    print("\n📡 Task: BRAINSTORM_IDEA")
    idea_prompt = """Generate a novel research idea for the llmXive platform that combines:
- Neural signal processing (EEG/MEG)
- Large language models
- Real-time applications

Provide:
1. A concise title
2. Brief description (2-3 sentences)
3. Key innovation
4. Potential impact"""
    
    response = conv_mgr.query_model(idea_prompt, task_type="BRAINSTORM_IDEA")
    print("Response:")
    print(response[:500] + "..." if len(response) > 500 else response)
    
    # Task 2: Technical Design
    print("\n\n📐 Task: WRITE_TECHNICAL_DESIGN")
    design_prompt = """Create a technical design outline for a system that:
- Uses EEG signals to detect cognitive load
- Adapts LLM responses based on user state
- Works in real-time

Include:
1. System architecture
2. Key components
3. Data flow"""
    
    response = conv_mgr.query_model(design_prompt, task_type="WRITE_TECHNICAL_DESIGN")
    print("Response:")
    print(response[:500] + "..." if len(response) > 500 else response)
    
    # Task 3: Implementation Planning
    print("\n\n🔧 Task: WRITE_IMPLEMENTATION_PLAN")
    plan_prompt = """Create an implementation plan for:
Project: Real-time EEG-based cognitive load detection

Break down into:
1. Phase 1: Data collection setup
2. Phase 2: Model development
3. Phase 3: Integration

For each phase, list key tasks."""
    
    response = conv_mgr.query_model(plan_prompt, task_type="WRITE_IMPLEMENTATION_PLAN")
    print("Response:")
    print(response[:500] + "..." if len(response) > 500 else response)
    
    # 5. Show model capabilities
    print("\n\n4. Model Information:")
    print("-" * 80)
    print(f"Model: {model.name_or_path}")
    print(f"Parameters: ~{model.num_parameters() / 1e9:.1f}B")
    print(f"Device: {next(model.parameters()).device}")
    print(f"Quantization: 4-bit (if GPU available)")
    
    # 6. Performance metrics
    print("\n5. Performance Notes:")
    print("-" * 80)
    print("✓ Running locally allows larger models (up to 20GB)")
    print("✓ Better quality responses than CI/CD models")
    print("✓ Supports all 40+ llmXive task types")
    print("✓ Can process longer contexts")
    
    print("\n✨ Demo complete! The system is ready for local automation tasks.")
    print("\nTo run the full automation:")
    print("  python cli.py --model-size-gb 20 --max-tasks 5")
    print("\nTo use a specific model:")
    print("  python cli.py --model 'microsoft/Phi-3-medium-4k-instruct' --max-tasks 3")

if __name__ == "__main__":
    demo_local_execution()