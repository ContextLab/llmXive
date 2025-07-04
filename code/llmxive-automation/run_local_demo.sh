#!/bin/bash
# Demo script for running llmXive automation locally with a larger model

echo "=== llmXive Local Automation Demo ==="
echo "This script demonstrates running the automation system locally with a larger model"
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Export environment variables (user should set these)
if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: Please set GITHUB_TOKEN environment variable"
    echo "Example: export GITHUB_TOKEN=your_github_token"
    exit 1
fi

# Optional: HuggingFace token for private models
if [ -z "$HF_TOKEN" ]; then
    echo "Note: HF_TOKEN not set. This is optional but recommended for better model access."
fi

echo ""
echo "Running llmXive automation with a larger model..."
echo "Using microsoft/Phi-3-medium-4k-instruct (4B parameters, ~8GB)"
echo ""

# Run with specific model and increased size limit
python cli.py \
    --model "microsoft/Phi-3-medium-4k-instruct" \
    --model-size-gb 20 \
    --max-tasks 3 \
    --verbose

# Alternative: Run with automatic model selection but higher size limit
# python cli.py --model-size-gb 20 --max-tasks 3 --verbose

# Example: Run a specific task with a larger model
# python cli.py \
#     --model "meta-llama/Llama-2-7b-chat-hf" \
#     --model-size-gb 20 \
#     --task BRAINSTORM_IDEA \
#     --verbose

echo ""
echo "Demo complete! Check logs/ directory for detailed execution logs."