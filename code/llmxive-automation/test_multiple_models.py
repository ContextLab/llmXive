#!/usr/bin/env python3
"""
Comprehensive test script for multiple LLM models under 20GB
Tests model loading, response generation, and parsing for all pipeline tasks
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append('src')

from model_manager import ModelManager
from conversation_manager import ConversationManager
from response_parser import ResponseParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiModelTester:
    """Test suite for multiple LLM models"""
    
    def __init__(self, max_size_gb: float = 20):
        """Initialize tester with size constraints"""
        self.max_size_gb = max_size_gb
        self.parser = ResponseParser()
        
        # Top 10 instruct-tuned models under 20GB (2025)
        self.test_models = [
            # Qwen models
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-3B-Instruct", 
            "Qwen/Qwen2.5-1.5B-Instruct",
            "Qwen/Qwen2.5-0.5B-Instruct",
            
            # Llama models
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Llama-3.2-1B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            
            # Microsoft Phi models
            "microsoft/Phi-3-mini-4k-instruct",
            "microsoft/Phi-3.5-mini-instruct",
            
            # Mistral models
            "mistralai/Mistral-7B-Instruct-v0.3",
            
            # Google Gemma models
            "google/gemma-2-2b-it",
            
            # HuggingFace Zephyr
            "HuggingFaceH4/zephyr-7b-beta",
            
            # Fallback (always works)
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        ]
        
        # Test prompts for different task types
        self.test_prompts = {
            "BRAINSTORM_IDEA": "Complete this research idea for the field of computer science:\n\nField: computer science\nIdea:",
            
            "REVIEW_TECHNICAL_DESIGN": """Task: Review this technical design document for a research project.

Design Document:
# Technical Design: Automated Bug Detection System

## Abstract
This project aims to develop an AI-powered system for automatically detecting bugs in software code using machine learning techniques.

## Introduction
Software bugs are a major challenge in development. This system will use neural networks to identify potential issues before they reach production.

## Proposed Approach
1. Train on large codebase with known bugs
2. Use transformer architecture for code analysis
3. Implement real-time scanning capabilities

## Implementation Strategy
- Data collection from open source repositories
- Model training using PyTorch
- Integration with popular IDEs

## Evaluation Plan
- Test on benchmark datasets
- Measure precision and recall
- User studies with developers

Evaluate the design on these criteria:
1. **Clarity**: Is the research question and approach clearly defined?
2. **Feasibility**: Can this be realistically implemented?
3. **Novelty**: Does this advance the field in a meaningful way?
4. **Methodology**: Is the proposed method sound and rigorous?
5. **Impact**: What is the potential contribution to science?

Provide:
- 3-5 specific strengths
- 3-5 specific concerns or suggestions
- Overall recommendation with score

Output format:
Strengths:
- [Strength 1]
- [Strength 2]
- [Strength 3]

Concerns:
- [Concern 1]
- [Concern 2]
- [Concern 3]

Recommendation: [Strong Accept/Accept/Weak Accept/Reject]
Score: [1.0/0.7/0.3/0.0]
Summary: [1-2 sentence overall assessment]""",

            "WRITE_CODE": """Task: Write Python code for a specific module following this implementation plan.

Module to implement: data_preprocessor

Write clean, well-documented Python code that:
1. Follows the plan specifications exactly
2. Includes comprehensive docstrings (Google style)
3. Has proper error handling
4. Uses type hints
5. Is modular and testable

Output the complete module code:""",

            "WRITE_ABSTRACT": """Task: Write an abstract for a scientific paper.

Available sections:
Introduction: This study investigates the use of machine learning for automated code review...
Methods: We developed a transformer-based model trained on 10M code samples...
Results: Our system achieved 85% precision and 92% recall on bug detection...

Write a 150-250 word abstract that includes:
1. **Background** - Why this research matters (1-2 sentences)
2. **Objective** - What this study aims to do (1 sentence)
3. **Methods** - How the research was conducted (2-3 sentences)
4. **Results** - Key findings (2-3 sentences)
5. **Conclusions** - What the findings mean (1-2 sentences)

Make it concise, informative, and self-contained."""
        }
        
        self.results = {}
        
    def test_model_loading(self, model_id: str) -> Dict[str, Any]:
        """Test if a model loads successfully"""
        logger.info(f"Testing model loading: {model_id}")
        
        start_time = time.time()
        try:
            mm = ModelManager(max_size_gb=self.max_size_gb)
            model, tokenizer = mm._load_model(model_id)
            load_time = time.time() - start_time
            
            return {
                "success": True,
                "load_time": load_time,
                "model_name": model.name_or_path if hasattr(model, 'name_or_path') else model_id,
                "tokenizer_class": tokenizer.__class__.__name__
            }
            
        except Exception as e:
            load_time = time.time() - start_time
            logger.error(f"Failed to load {model_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "load_time": load_time
            }
    
    def test_model_generation(self, model_id: str, task_type: str, prompt: str) -> Dict[str, Any]:
        """Test model response generation for a specific task"""
        logger.info(f"Testing {model_id} on {task_type}")
        
        try:
            mm = ModelManager(max_size_gb=self.max_size_gb)
            model, tokenizer = mm._load_model(model_id)
            cm = ConversationManager(model, tokenizer)
            
            start_time = time.time()
            response = cm.query_model(prompt, task_type=task_type)
            generation_time = time.time() - start_time
            
            if response:
                # Test parsing
                parse_success = False
                parsed_result = None
                
                try:
                    if task_type == "REVIEW_TECHNICAL_DESIGN":
                        parsed_result = self.parser.parse_review_response(response)
                        parse_success = parsed_result is not None
                    elif task_type == "BRAINSTORM_IDEA":
                        parsed_result = self.parser.parse_brainstorm_response(response)
                        parse_success = parsed_result is not None
                    else:
                        # For other tasks, just check if we got content
                        parse_success = len(response.strip()) > 10
                        parsed_result = {"content": response[:200] + "..." if len(response) > 200 else response}
                        
                except Exception as e:
                    logger.warning(f"Parsing failed for {model_id} on {task_type}: {e}")
                
                return {
                    "success": True,
                    "response_length": len(response),
                    "generation_time": generation_time,
                    "parse_success": parse_success,
                    "parsed_result": parsed_result,
                    "response_preview": response[:200] + "..." if len(response) > 200 else response
                }
            else:
                return {
                    "success": False,
                    "error": "No response generated",
                    "generation_time": generation_time
                }
                
        except Exception as e:
            logger.error(f"Generation test failed for {model_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive tests on all models"""
        logger.info("Starting comprehensive model testing...")
        
        overall_results = {
            "timestamp": datetime.now().isoformat(),
            "max_size_gb": self.max_size_gb,
            "models_tested": len(self.test_models),
            "tasks_tested": list(self.test_prompts.keys()),
            "results": {}
        }
        
        for model_id in self.test_models:
            logger.info(f"\\n{'='*60}")
            logger.info(f"Testing model: {model_id}")
            logger.info('='*60)
            
            model_results = {
                "model_id": model_id,
                "loading": None,
                "tasks": {}
            }
            
            # Test model loading
            loading_result = self.test_model_loading(model_id)
            model_results["loading"] = loading_result
            
            if loading_result["success"]:
                logger.info(f"✅ Model loaded successfully in {loading_result['load_time']:.2f}s")
                
                # Test each task type
                for task_type, prompt in self.test_prompts.items():
                    logger.info(f"Testing task: {task_type}")
                    
                    task_result = self.test_model_generation(model_id, task_type, prompt)
                    model_results["tasks"][task_type] = task_result
                    
                    if task_result["success"]:
                        if task_result.get("parse_success", False):
                            logger.info(f"✅ {task_type}: Generated and parsed successfully")
                        else:
                            logger.info(f"⚠️  {task_type}: Generated but parsing failed")
                    else:
                        logger.info(f"❌ {task_type}: Generation failed")
            else:
                logger.error(f"❌ Model loading failed: {loading_result['error']}")
            
            overall_results["results"][model_id] = model_results
        
        return overall_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        report = f"""# Multi-Model Test Report
        
**Date**: {results['timestamp']}
**Models Tested**: {results['models_tested']}
**Max Size**: {results['max_size_gb']}GB
**Tasks**: {', '.join(results['tasks_tested'])}

## Summary

"""
        
        successful_loads = 0
        total_task_successes = 0
        total_parse_successes = 0
        total_tasks = 0
        
        for model_id, model_result in results["results"].items():
            if model_result["loading"]["success"]:
                successful_loads += 1
                
                for task_type, task_result in model_result["tasks"].items():
                    total_tasks += 1
                    if task_result["success"]:
                        total_task_successes += 1
                        if task_result.get("parse_success", False):
                            total_parse_successes += 1
        
        report += f"""
- **Models loaded successfully**: {successful_loads}/{results['models_tested']} ({successful_loads/results['models_tested']*100:.1f}%)
- **Task generations successful**: {total_task_successes}/{total_tasks} ({total_task_successes/total_tasks*100:.1f}%)
- **Parsing successful**: {total_parse_successes}/{total_tasks} ({total_parse_successes/total_tasks*100:.1f}%)

## Detailed Results

"""
        
        for model_id, model_result in results["results"].items():
            model_name = model_id.split('/')[-1]
            report += f"### {model_name}\n\n"
            
            if model_result["loading"]["success"]:
                load_time = model_result["loading"]["load_time"]
                report += f"✅ **Loading**: Success ({load_time:.2f}s)\\n\\n"
                
                report += "**Task Results**:\\n"
                for task_type, task_result in model_result["tasks"].items():
                    if task_result["success"]:
                        gen_time = task_result["generation_time"]
                        response_len = task_result["response_length"]
                        parse_status = "✅ Parsed" if task_result.get("parse_success", False) else "⚠️ Parse Failed"
                        report += f"- **{task_type}**: ✅ Generated ({gen_time:.2f}s, {response_len} chars) {parse_status}\\n"
                    else:
                        error = task_result.get("error", "Unknown error")
                        report += f"- **{task_type}**: ❌ Failed - {error}\\n"
            else:
                error = model_result["loading"]["error"]
                report += f"❌ **Loading**: Failed - {error}\\n"
            
            report += "\\n"
        
        return report
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to files"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_model_test_{timestamp}"
        
        # Save JSON results
        json_file = f"{filename}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save markdown report
        report = self.generate_report(results)
        md_file = f"{filename}.md"
        with open(md_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Results saved to {json_file} and {md_file}")
        return json_file, md_file

def main():
    """Main test runner"""
    logger.info("🚀 Starting Multi-Model Test Suite")
    
    tester = MultiModelTester(max_size_gb=20)
    results = tester.run_comprehensive_test()
    
    # Save results
    json_file, md_file = tester.save_results(results)
    
    logger.info("\\n" + "="*60)
    logger.info("🎉 Testing complete!")
    logger.info(f"📄 Results: {json_file}")
    logger.info(f"📊 Report: {md_file}")
    logger.info("="*60)

if __name__ == "__main__":
    main()