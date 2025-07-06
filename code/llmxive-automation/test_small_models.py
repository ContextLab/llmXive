#!/usr/bin/env python3
"""
Test script for top 10 highest-ranked instruct models under 3GB
Tests loading, generation, and parsing across multiple task types
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmallModelTester:
    """Test suite for small instruct models under 3GB"""
    
    def __init__(self):
        """Initialize tester with 3GB limit"""
        self.max_size_gb = 3.0
        self.parser = ResponseParser()
        
        # Top 10 highest-ranked instruct models under 3GB (2025)
        # Ordered by popularity/performance based on HuggingFace rankings
        self.test_models = [
            # Qwen series (most popular small models)
            "Qwen/Qwen2.5-1.5B-Instruct",      # 1.5B - highly rated
            "Qwen/Qwen2.5-0.5B-Instruct",      # 0.5B - smallest Qwen
            
            # Google Gemma series (Google's small models)
            "google/gemma-2-2b-it",            # 2B - Google's instruction model
            
            # Microsoft Phi series (high performance small models)
            "microsoft/Phi-3-mini-4k-instruct", # 3.8B - Microsoft's best small model
            "microsoft/Phi-3.5-mini-instruct",  # 3.8B - Latest Phi
            
            # Meta Llama series (small versions)
            "meta-llama/Llama-3.2-1B-Instruct", # 1B - Latest Llama small
            "meta-llama/Llama-3.2-3B-Instruct", # 3B - Llama 3.2 medium
            
            # Other highly-rated small models
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0", # 1.1B - Reliable fallback
            "stabilityai/stablelm-2-1_6b-chat",   # 1.6B - Stability AI
            "HuggingFaceH4/zephyr-7b-beta",       # 7B but often under 3GB with quantization
        ]
        
        # Comprehensive test prompts for different capabilities
        self.test_prompts = {
            "code_generation": {
                "prompt": """Write a Python function that calculates the factorial of a number using recursion. Include proper error handling and docstring.""",
                "task_type": "WRITE_CODE",
                "expected_keywords": ["def", "factorial", "recursion", "return"]
            },
            
            "scientific_reasoning": {
                "prompt": """Explain the process of photosynthesis in plants, including the chemical equation and the role of chlorophyll. Be scientific and accurate.""",
                "task_type": "WRITE_METHODS", 
                "expected_keywords": ["photosynthesis", "chlorophyll", "CO2", "glucose", "light"]
            },
            
            "review_task": {
                "prompt": """Review this research proposal:

Title: Machine Learning for Protein Folding Prediction
Abstract: This study proposes using transformer neural networks to predict protein 3D structure from amino acid sequences.

Evaluate:
1. Scientific merit and novelty
2. Technical feasibility 
3. Potential impact

Provide: Strengths, Concerns, Recommendation (Accept/Reject), Score (0.0-1.0)""",
                "task_type": "REVIEW_TECHNICAL_DESIGN",
                "expected_keywords": ["strength", "concern", "recommend", "score", "protein"]
            },
            
            "math_reasoning": {
                "prompt": """Solve this step by step: If a train travels 120 km in 2 hours, then speeds up by 20 km/h for the next 3 hours, what is the total distance traveled?""",
                "task_type": "BRAINSTORM_IDEA",
                "expected_keywords": ["120", "distance", "speed", "total", "km"]
            },
            
            "creative_writing": {
                "prompt": """Write a short abstract for a fictional research paper about discovering a new species of bioluminescent bacteria in deep ocean vents.""",
                "task_type": "WRITE_ABSTRACT",
                "expected_keywords": ["species", "bioluminescent", "bacteria", "ocean", "discovered"]
            }
        }
        
        self.results = {}
        
    def test_model_loading(self, model_id: str) -> Dict[str, Any]:
        """Test if a model loads successfully within size limits"""
        logger.info(f"🔄 Testing model loading: {model_id}")
        
        start_time = time.time()
        try:
            mm = ModelManager(max_size_gb=self.max_size_gb)
            model, tokenizer = mm._load_model(model_id)
            load_time = time.time() - start_time
            
            # Get model info
            model_info = {
                "success": True,
                "load_time": load_time,
                "model_name": getattr(model, 'name_or_path', model_id),
                "tokenizer_class": tokenizer.__class__.__name__,
                "vocab_size": tokenizer.vocab_size if hasattr(tokenizer, 'vocab_size') else 'unknown'
            }
            
            # Try to get model size info
            try:
                num_params = sum(p.numel() for p in model.parameters())
                model_info["num_parameters"] = num_params
                model_info["num_parameters_str"] = f"{num_params/1e9:.2f}B" if num_params > 1e9 else f"{num_params/1e6:.1f}M"
            except:
                model_info["num_parameters"] = "unknown"
                model_info["num_parameters_str"] = "unknown"
            
            logger.info(f"✅ Loaded successfully in {load_time:.2f}s - {model_info.get('num_parameters_str', 'unknown')} params")
            return model_info
            
        except Exception as e:
            load_time = time.time() - start_time
            logger.error(f"❌ Failed to load {model_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "load_time": load_time
            }
    
    def test_model_generation(self, model_id: str, test_name: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test model response generation for a specific task"""
        logger.info(f"🧪 Testing {model_id} on {test_name}")
        
        try:
            mm = ModelManager(max_size_gb=self.max_size_gb)
            model, tokenizer = mm._load_model(model_id)
            cm = ConversationManager(model, tokenizer)
            
            start_time = time.time()
            response = cm.query_model(
                test_config["prompt"], 
                task_type=test_config["task_type"]
            )
            generation_time = time.time() - start_time
            
            if response:
                # Basic response analysis
                response_len = len(response)
                word_count = len(response.split())
                
                # Check for expected keywords
                expected_keywords = test_config.get("expected_keywords", [])
                found_keywords = [kw for kw in expected_keywords if kw.lower() in response.lower()]
                keyword_score = len(found_keywords) / len(expected_keywords) if expected_keywords else 1.0
                
                # Test parsing
                parse_success = False
                parsed_result = None
                
                try:
                    if test_config["task_type"] == "REVIEW_TECHNICAL_DESIGN":
                        parsed_result = self.parser.parse_review_response(response)
                        parse_success = parsed_result is not None
                    elif test_config["task_type"] == "BRAINSTORM_IDEA":
                        parsed_result = self.parser.parse_brainstorm_response(response)
                        parse_success = parsed_result is not None
                    else:
                        # For other tasks, check basic quality
                        parse_success = len(response.strip()) > 20
                        parsed_result = {"preview": response[:100] + "..." if len(response) > 100 else response}
                        
                except Exception as e:
                    logger.warning(f"⚠️  Parsing failed: {e}")
                
                result = {
                    "success": True,
                    "response_length": response_len,
                    "word_count": word_count,
                    "generation_time": generation_time,
                    "keyword_score": keyword_score,
                    "found_keywords": found_keywords,
                    "parse_success": parse_success,
                    "parsed_result": parsed_result,
                    "response_preview": response[:200] + "..." if len(response) > 200 else response
                }
                
                # Quality assessment
                if keyword_score >= 0.7 and parse_success and word_count >= 10:
                    logger.info(f"✅ {test_name}: Excellent response")
                elif keyword_score >= 0.4 and word_count >= 5:
                    logger.info(f"🟡 {test_name}: Good response")
                else:
                    logger.info(f"🔶 {test_name}: Basic response")
                
                return result
            else:
                return {
                    "success": False,
                    "error": "No response generated",
                    "generation_time": generation_time
                }
                
        except Exception as e:
            logger.error(f"❌ Generation test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive tests on all small models"""
        logger.info("🚀 Starting comprehensive small model testing...")
        logger.info(f"📏 Size limit: {self.max_size_gb}GB")
        logger.info(f"🔢 Models to test: {len(self.test_models)}")
        logger.info(f"🧪 Test types: {list(self.test_prompts.keys())}")
        
        overall_results = {
            "timestamp": datetime.now().isoformat(),
            "max_size_gb": self.max_size_gb,
            "models_tested": len(self.test_models),
            "test_types": list(self.test_prompts.keys()),
            "results": {}
        }
        
        for i, model_id in enumerate(self.test_models, 1):
            logger.info(f"\\n{'='*80}")
            logger.info(f"🎯 Testing model {i}/{len(self.test_models)}: {model_id}")
            logger.info('='*80)
            
            model_results = {
                "model_id": model_id,
                "loading": None,
                "tests": {}
            }
            
            # Test model loading
            loading_result = self.test_model_loading(model_id)
            model_results["loading"] = loading_result
            
            if loading_result["success"]:
                # Test each task type
                for test_name, test_config in self.test_prompts.items():
                    test_result = self.test_model_generation(model_id, test_name, test_config)
                    model_results["tests"][test_name] = test_result
            else:
                logger.error(f"❌ Skipping tests due to loading failure")
            
            overall_results["results"][model_id] = model_results
        
        return overall_results
    
    def generate_detailed_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed performance report"""
        report = f"""# Small Model Performance Report (Under {results['max_size_gb']}GB)
        
**Date**: {results['timestamp']}
**Models Tested**: {results['models_tested']}
**Test Types**: {', '.join(results['test_types'])}

## Executive Summary

"""
        
        # Calculate summary statistics
        successful_loads = 0
        total_tests = 0
        successful_generations = 0
        successful_parses = 0
        avg_load_times = []
        avg_gen_times = []
        
        model_scores = {}
        
        for model_id, model_result in results["results"].items():
            model_name = model_id.split('/')[-1]
            
            if model_result["loading"]["success"]:
                successful_loads += 1
                avg_load_times.append(model_result["loading"]["load_time"])
                
                test_score = 0
                test_count = 0
                
                for test_name, test_result in model_result["tests"].items():
                    total_tests += 1
                    test_count += 1
                    
                    if test_result["success"]:
                        successful_generations += 1
                        avg_gen_times.append(test_result["generation_time"])
                        
                        # Calculate test score
                        score = 0
                        if test_result.get("parse_success", False):
                            successful_parses += 1
                            score += 0.4
                        
                        keyword_score = test_result.get("keyword_score", 0)
                        score += keyword_score * 0.4
                        
                        if test_result.get("word_count", 0) >= 20:
                            score += 0.2
                        
                        test_score += score
                
                model_scores[model_name] = test_score / test_count if test_count > 0 else 0
        
        # Sort models by performance
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        report += f"""
- **Loading Success Rate**: {successful_loads}/{results['models_tested']} ({successful_loads/results['models_tested']*100:.1f}%)
- **Generation Success Rate**: {successful_generations}/{total_tests} ({successful_generations/total_tests*100:.1f}%)
- **Parsing Success Rate**: {successful_parses}/{total_tests} ({successful_parses/total_tests*100:.1f}%)
- **Average Load Time**: {sum(avg_load_times)/len(avg_load_times):.2f}s
- **Average Generation Time**: {sum(avg_gen_times)/len(avg_gen_times):.2f}s

## 🏆 Model Rankings (by overall performance)

"""
        
        for i, (model_name, score) in enumerate(sorted_models[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            report += f"{medal} **{model_name}**: {score:.3f}\\n"
        
        report += "\\n## Detailed Results\\n\\n"
        
        for model_id, model_result in results["results"].items():
            model_name = model_id.split('/')[-1]
            report += f"### {model_name}\\n\\n"
            
            if model_result["loading"]["success"]:
                loading = model_result["loading"]
                params = loading.get("num_parameters_str", "unknown")
                load_time = loading["load_time"]
                vocab_size = loading.get("vocab_size", "unknown")
                
                report += f"✅ **Loading**: Success ({load_time:.2f}s, {params} params, {vocab_size} vocab)\\n\\n"
                
                report += "**Test Results**:\\n"
                for test_name, test_result in model_result["tests"].items():
                    if test_result["success"]:
                        gen_time = test_result["generation_time"]
                        word_count = test_result["word_count"]
                        keyword_score = test_result.get("keyword_score", 0)
                        parse_status = "✅" if test_result.get("parse_success", False) else "❌"
                        
                        report += f"- **{test_name}**: ✅ Generated ({gen_time:.2f}s, {word_count} words, {keyword_score:.1%} keywords) {parse_status}\\n"
                    else:
                        error = test_result.get("error", "Unknown error")
                        report += f"- **{test_name}**: ❌ Failed - {error}\\n"
            else:
                error = model_result["loading"]["error"]
                report += f"❌ **Loading**: Failed - {error}\\n"
            
            report += "\\n"
        
        return report
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to files"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"small_model_test_{timestamp}"
        
        # Save JSON results
        json_file = f"{filename}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save markdown report
        report = self.generate_detailed_report(results)
        md_file = f"{filename}.md"
        with open(md_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Results saved to {json_file} and {md_file}")
        return json_file, md_file

def main():
    """Main test runner"""
    logger.info("🚀 Starting Small Model Test Suite (Under 3GB)")
    
    tester = SmallModelTester()
    results = tester.run_comprehensive_test()
    
    # Save results
    json_file, md_file = tester.save_results(results)
    
    logger.info("\\n" + "="*80)
    logger.info("🎉 Small model testing complete!")
    logger.info(f"📄 JSON Results: {json_file}")
    logger.info(f"📊 Detailed Report: {md_file}")
    
    # Print quick summary
    successful_loads = sum(1 for r in results['results'].values() if r['loading']['success'])
    total_tests = sum(len(r['tests']) for r in results['results'].values() if r['loading']['success'])
    successful_tests = sum(
        sum(1 for t in r['tests'].values() if t['success']) 
        for r in results['results'].values() if r['loading']['success']
    )
    
    logger.info(f"📈 Summary: {successful_loads}/{len(tester.test_models)} models loaded, {successful_tests}/{total_tests} tests passed")
    logger.info("="*80)

if __name__ == "__main__":
    main()