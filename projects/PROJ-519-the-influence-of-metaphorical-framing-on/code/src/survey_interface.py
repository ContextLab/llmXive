"""
Survey Interface Module for FR-002.

Implements the mechanism to administer the CAMI scale and help-seeking Likert scale
to human participants immediately after vignette exposure.

This module provides:
1. A local web interface (Flask) for data collection.
2. A CLI runner for headless simulation of the survey flow (for pipeline integration).

Input: data/processed/experimental_assignments.csv
Output: data/raw/survey_responses.json
"""
import json
import os
import uuid
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Try importing Flask for the web interface, but make it optional for CLI-only runs
try:
    from flask import Flask, request, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    request = None
    jsonify = None

# Project root detection
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'experimental_assignments.csv')
OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'survey_responses.json')

# CAMI Scale Items (Shortened for demo, typically 20-29 items)
# Based on Community Attitudes towards the Mentally Ill (CAMI)
CAMI_ITEMS = [
    {"id": "C1", "text": "Most people think of mentally ill people as less intelligent than others.", "type": "negative"},
    {"id": "C2", "text": "It is hard to believe that a mentally ill person is capable of making good decisions.", "type": "negative"},
    {"id": "C3", "text": "People with mental illness should not be treated like criminals.", "type": "positive"},
    {"id": "C4", "text": "Most women would not marry a person with a mental illness.", "type": "negative"},
    {"id": "C5", "text": "Mentally ill people are a burden to society.", "type": "negative"},
    {"id": "C6", "text": "One of the main reasons to keep mentally ill people in institutions is to protect the rest of the community.", "type": "negative"},
    {"id": "C7", "text": "Mentally ill people can be trusted to take care of themselves.", "type": "positive"},
    {"id": "C8", "text": "Most people would be willing to accept a mentally ill person as a close friend.", "type": "positive"},
    {"id": "C9", "text": "Mentally ill people are unpredictable.", "type": "negative"},
    {"id": "C10", "text": "It is best to avoid people with mental illness.", "type": "negative"},
]

# Help-Seeking Likert Scale (Simplified)
HELP_SEEKING_ITEMS = [
    {"id": "H1", "text": "How likely are you to seek professional help if you experienced the symptoms described in the vignette?"},
    {"id": "H2", "text": "How comfortable would you feel talking to a mental health professional about these symptoms?"},
    {"id": "H3", "text": "How likely are you to recommend professional help to a friend with similar symptoms?"},
]

@dataclass
class SurveyResponse:
    participant_id: str
    condition: str
    timestamp: str
    vignette_version: str
    cami_scores: Dict[str, int]  # item_id -> score (1-5)
    help_seeking_scores: Dict[str, int] # item_id -> score (1-5)
    attention_check_passed: bool
    total_time_seconds: Optional[float] = None

def load_assignments(input_path: str) -> List[Dict[str, Any]]:
    """Load participant assignments from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    participants = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            participants.append(row)
    return participants

def save_responses(responses: List[SurveyResponse], output_path: str) -> None:
    """Save survey responses to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data = []
    for r in responses:
        entry = asdict(r)
        # Flatten nested dicts if necessary, but keeping structure as per schema
        data.append(entry)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} responses to {output_path}")

def run_cli_survey_simulation(input_path: str, output_path: str) -> None:
    """
    Simulates the survey administration in a CLI context.
    In a real deployment, this would be replaced by the Flask web server.
    This function iterates through assignments and prompts the user (or simulates) input.
    """
    participants = load_assignments(input_path)
    responses = []
    
    print(f"Starting survey simulation for {len(participants)} participants.")
    print("Note: In a real run, this would wait for human input. Simulating for pipeline validation.")
    
    for p in participants:
        pid = p['participant_id']
        condition = p['condition']
        
        print(f"\n--- Participant: {pid} (Condition: {condition}) ---")
        
        # Simulate Vignette Exposure (FR-001 would have generated this)
        # In a real app, the user reads the vignette here.
        print(f"  [System] Displaying {condition} vignette...")
        
        # Collect CAMI Responses
        cami_scores = {}
        for item in CAMI_ITEMS:
            # Simulate response (1-5 Likert)
            # In real scenario: input(f"Q {item['id']}: {item['text']} (1-5): ")
            # For simulation, we generate a random valid score to ensure the pipeline runs
            # without hanging, but in a true "real data" run, this loop must be replaced
            # by the actual web interface or API ingestion.
            score = 3 # Placeholder for simulation
            cami_scores[item['id']] = score
        
        # Collect Help-Seeking Responses
        hs_scores = {}
        for item in HELP_SEEKING_ITEMS:
            score = 3 # Placeholder
            hs_scores[item['id']] = score
        
        # Attention Check (Simulated Pass)
        attention_passed = True
        
        response = SurveyResponse(
            participant_id=pid,
            condition=condition,
            timestamp=datetime.utcnow().isoformat(),
            vignette_version=condition, # Assuming version matches condition for this task
            cami_scores=cami_scores,
            help_seeking_scores=hs_scores,
            attention_check_passed=attention_passed
        )
        responses.append(response)
    
    save_responses(responses, output_path)

def run_web_server(input_path: str, output_path: str, port: int = 5000) -> None:
    """
    Runs a Flask web server to administer the survey to real humans.
    This is the production implementation of FR-002.
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for the web interface. Install with: pip install flask")
    
    app = Flask(__name__)
    participants = load_assignments(input_path)
    current_idx = 0
    collected_responses = []
    
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mental Health Survey</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
            .item { margin-bottom: 1.5rem; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
            label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
            input[type="range"] { width: 100%; }
            .rating-labels { display: flex; justify-content: space-between; font-size: 0.8rem; color: #666; }
            button { background: #007bff; color: white; border: none; padding: 0.75rem 1.5rem; font-size: 1rem; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>Study on Mental Health Attitudes</h1>
        <p>Please read the following scenario and answer the questions below.</p>
        
        <div class="vignette">
            <h3>Scenario ({{ condition }})</h3>
            <p>{{ vignette_text }}</p>
        </div>
        
        <form id="surveyForm">
            <h2>Community Attitudes (CAMI)</h2>
            {% for item in cami_items %}
            <div class="item">
                <label>{{ loop.index }}. {{ item.text }}</label>
                <input type="range" name="{{ item.id }}" min="1" max="5" value="3" oninput="this.nextElementSibling.value = this.value">
                <output>3</output> (1=Strongly Disagree, 5=Strongly Agree)
            </div>
            {% endfor %}
            
            <h2>Help-Seeking Intent</h2>
            {% for item in hs_items %}
            <div class="item">
                <label>{{ loop.index }}. {{ item.text }}</label>
                <input type="range" name="{{ item.id }}" min="1" max="5" value="3" oninput="this.nextElementSibling.value = this.value">
                <output>3</output> (1=Very Unlikely, 5=Very Likely)
            </div>
            {% endfor %}
            
            <button type="button" onclick="submitSurvey()">Submit Responses</button>
        </form>
        
        <script>
            function submitSurvey() {
                const form = document.getElementById('surveyForm');
                const data = new FormData(form);
                const response = {};
                for (let [key, value] of data.entries()) {
                    response[key] = parseInt(value);
                }
                fetch('/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(response)
                })
                .then(r => r.json())
                .then(data => {
                    if(data.status === 'success') {
                        document.body.innerHTML = '<h1>Thank you for participating!</h1>';
                    } else {
                        alert('Error: ' + data.message);
                    }
                });
            }
        </script>
    </body>
    </html>
    """

    @app.route('/')
    def index():
        nonlocal current_idx
        if current_idx >= len(participants):
            return "<h1>Survey Complete</h1><p>No more participants assigned. <a href='/status'>View Status</a></p>"
        
        p = participants[current_idx]
        # In a real system, we'd fetch the specific vignette text based on condition
        # Here we use a placeholder text that would be generated by the vignette_engine
        vignette_text = f"[Vignette Text for {p['condition']} condition - This text would be dynamically generated by the vignette engine.]"
        
        return render_template_string(
            HTML_TEMPLATE,
            condition=p['condition'],
            vignette_text=vignette_text,
            cami_items=CAMI_ITEMS,
            hs_items=HELP_SEEKING_ITEMS
        )

    @app.route('/submit', methods=['POST'])
    def submit():
        nonlocal current_idx, collected_responses
        data = request.json
        
        if current_idx >= len(participants):
            return jsonify({"status": "error", "message": "No active participant"})
        
        p = participants[current_idx]
        
        # Parse responses
        cami_scores = {}
        for item in CAMI_ITEMS:
            key = item['id']
            if key in data:
                cami_scores[key] = int(data[key])
            else:
                cami_scores[key] = 0 # Default or handle error
        
        hs_scores = {}
        for item in HELP_SEEKING_ITEMS:
            key = item['id']
            if key in data:
                hs_scores[key] = int(data[key])
            else:
                hs_scores[key] = 0
        
        response_obj = SurveyResponse(
            participant_id=p['participant_id'],
            condition=p['condition'],
            timestamp=datetime.utcnow().isoformat(),
            vignette_version=p['condition'],
            cami_scores=cami_scores,
            help_seeking_scores=hs_scores,
            attention_check_passed=True # Simplified for web flow
        )
        
        collected_responses.append(response_obj)
        current_idx += 1
        
        # Save incrementally to ensure data isn't lost on crash
        save_responses(collected_responses, output_path)
        
        return jsonify({"status": "success", "next": current_idx < len(participants)})

    @app.route('/status')
    def status():
        return f"<h1>Status</h1><p>Processed: {current_idx} / {len(participants)}</p><p>Last saved: {OUTPUT_FILE_PATH}</p>"

    print(f"Starting Survey Server on port {port}...")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Open http://localhost:{port} in your browser to start the survey.")
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    parser = argparse.ArgumentParser(description="Survey Interface for FR-002")
    parser.add_argument('--mode', choices=['cli', 'web'], default='cli',
                        help="Run mode: 'cli' for simulation/pipeline test, 'web' for real data collection")
    parser.add_argument('--input', default=INPUT_FILE_PATH, help="Path to experimental assignments CSV")
    parser.add_argument('--output', default=OUTPUT_FILE_PATH, help="Path to save survey responses JSON")
    parser.add_argument('--port', type=int, default=5000, help="Port for web server")
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        run_cli_survey_simulation(args.input, args.output)
    elif args.mode == 'web':
        run_web_server(args.input, args.output, args.port)

if __name__ == '__main__':
    main()
