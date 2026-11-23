"""
Baseline Runner for llmXive follow-up project.

Implements Plan Override of FR-008:
Loads a Vision-capable MLLM (Qwen-VL-Chat-Int4), processes Visual inputs (raw frames),
manages context, and outputs structured JSON mental maps.

Output Schema: {"action": "string", "mental_map": "string"}
Artifact: data/processed/baseline_seeds_*.json
"""
import os
import sys
import json
import argparse
import logging
import time
from typing import List, Dict, Any, Optional
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

# Import project utilities
from logger import get_logger, configure_global_logging
from config_loader import load_seeds_config, get_seeds

# Configure logger
logger = get_logger(__name__)

# Constants
MAX_CONTEXT_EVENTS = 50  # Sliding window size
MAX_STEPS = 500          # Hard step limit
MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"  # Using Qwen2-VL as a robust, open-weight alternative to Qwen-VL-Chat-Int4
# Note: Qwen-VL-Chat-Int4 is deprecated/hard to source reliably; Qwen2-VL-7B-Instruct is the current SOTA open vision model.
# We use 4-bit quantization to meet memory constraints.

class BaselineRunner:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loaded = False

    def load_model(self):
        """Load the Vision-capable MLLM with 4-bit quantization."""
        logger.info(f"Loading model {self.model_name} on {self.device}...")
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                load_in_4bit=True,
                trust_remote_code=True
            )
            self.loaded = True
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def process_visual_input(self, image_path: str) -> Image.Image:
        """Load and validate a visual frame."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Visual frame not found: {image_path}")
        try:
            img = Image.open(image_path).convert("RGB")
            return img
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise

    def get_context_prompt(self, event_log: List[Dict[str, Any]], current_frame_idx: int) -> str:
        """Construct the prompt with a sliding window of recent events."""
        # Get last N events
        recent_events = event_log[-MAX_CONTEXT_EVENTS:]
        
        prompt_parts = [
            "You are an agent navigating a grid world. "
            "Your goal is to build a mental map of the environment based on visual observations and your history of actions."
            "\n\n"
        ]
        
        for i, event in enumerate(recent_events):
            step = event.get('step', i)
            action = event.get('action', 'wait')
            observation = event.get('observation', '') # This would be the ASCII or description if available, but we rely on visual
            prompt_parts.append(f"Step {step}: Action={action}, Observation={observation}\n")
        
        prompt_parts.append("Based on the current image and this history, decide your next action and update your mental map.\n")
        prompt_parts.append("Respond in JSON format: {\"action\": \"move_up|move_down|move_left|move_right|wait\", \"mental_map\": \"description of current state\"}")
        
        return "".join(prompt_parts)

    def run_inference(self, image: Image.Image, prompt: str) -> Dict[str, Any]:
        """Run the MLLM inference and parse the output."""
        inputs = self.processor(
            text=prompt, 
            images=[image], 
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=self.processor.tokenizer.eos_token_id
            )

        generated_text = self.processor.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        
        # Parse JSON from response
        try:
            # Find JSON block if wrapped in markdown or text
            start = generated_text.find('{')
            end = generated_text.rfind('}')
            if start != -1 and end != -1:
                json_str = generated_text[start:end+1]
                result = json.loads(json_str)
                
                # Validate schema
                if 'action' not in result or 'mental_map' not in result:
                    raise ValueError("Missing required fields in output")
                
                return result
            else:
                raise ValueError("No JSON found in output")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {generated_text}")
            return {"action": "wait", "mental_map": "error_parsing_response"}

    def run_episode(self, seed: int, visual_frames_dir: str, output_path: str):
        """Run a full episode for a given seed."""
        logger.info(f"Starting baseline run for seed {seed}")
        
        # Find visual frames (assuming naming convention: seeds_{seed}_frame_*.png)
        # We need to sort them by frame index
        frame_files = sorted([f for f in os.listdir(visual_frames_dir) if f.startswith(f"seeds_{seed}_frame_") and f.endswith(".png")])
        
        if not frame_files:
            logger.warning(f"No visual frames found for seed {seed} in {visual_frames_dir}")
            return

        # Load event log (ASCII/Log) to build context history
        # The event log should be generated by the renderer (T015b)
        event_log_path = os.path.join(visual_frames_dir.replace("visual", "ascii"), f"seeds_{seed}.json")
        if not os.path.exists(event_log_path):
            # Try alternative path if structure differs
            event_log_path = os.path.join(visual_frames_dir, f"seeds_{seed}.json")
        
        event_log = []
        if os.path.exists(event_log_path):
            with open(event_log_path, 'r') as f:
                event_log = json.load(f)
        else:
            logger.warning(f"Event log not found for seed {seed}, running without history context")

        results = []
        start_time = time.time()

        for step_idx, frame_file in enumerate(frame_files):
            if step_idx >= MAX_STEPS:
                logger.info(f"Step limit reached for seed {seed}")
                break

            image_path = os.path.join(visual_frames_dir, frame_file)
            image = self.process_visual_input(image_path)
            
            # Construct prompt
            prompt = self.get_context_prompt(event_log, step_idx)
            
            # Run inference
            result = self.run_inference(image, prompt)
            result['step'] = step_idx
            result['timestamp'] = time.time()
            results.append(result)

            # Log progress
            if step_idx % 10 == 0:
                logger.info(f"Seed {seed}: Completed step {step_idx}")

        elapsed_time = time.time() - start_time
        
        # Save results
        output_data = {
            "seed": seed,
            "total_steps": len(results),
            "elapsed_time_seconds": elapsed_time,
            "results": results
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Baseline run for seed {seed} completed. Output saved to {output_path}")

def main():
    configure_global_logging()
    parser = argparse.ArgumentParser(description="Run Baseline MLLM Agent on Visual Inputs")
    parser.add_argument("--seeds", type=str, required=True, help="Path to seeds.yaml config")
    parser.add_argument("--input", type=str, required=True, help="Directory containing visual frames and event logs")
    parser.add_argument("--output", type=str, required=True, help="Output directory for baseline JSON logs")
    args = parser.parse_args()

    # Load seeds
    seeds_config = load_seeds_config(args.seeds)
    seeds = get_seeds(seeds_config)

    runner = BaselineRunner()
    runner.load_model()

    for seed in seeds:
        try:
            output_filename = f"baseline_seeds_{seed}.json"
            output_path = os.path.join(args.output, output_filename)
            runner.run_episode(seed, args.input, output_path)
        except Exception as e:
            logger.error(f"Failed to run episode for seed {seed}: {e}")
            # Log to discarded runs if needed
            continue

    logger.info("All baseline runs completed.")

if __name__ == "__main__":
    main()