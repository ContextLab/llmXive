import streamlit as st
import os
import sys
import random
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path

# Add project root to path if running as script
if "code" not in sys.path[0]:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.helpers import (
    generate_user_id,
    hash_ip,
    check_duplicate_ip,
    save_submission,
    get_project_root
)
from utils.config import get_consent_file_path, load_consent_text

# Constants
IRB_PROTOCOL_ID = os.getenv("IRB_PROTOCOL_ID", "UNKNOWN")
LATIN_SQUARE_SEQUENCES = [
    ("Professional", "Minimalist", "Low-Quality", "Neutral"),
    ("Minimalist", "Low-Quality", "Neutral", "Professional"),
    ("Low-Quality", "Neutral", "Professional", "Minimalist"),
    ("Neutral", "Professional", "Minimalist", "Low-Quality"),
]

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = generate_user_id()
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'current_stimulus_idx' not in st.session_state:
        st.session_state.current_stimulus_idx = 0
    if 'sequence' not in st.session_state:
        # Select one sequence randomly
        st.session_state.sequence = random.choice(LATIN_SQUARE_SEQUENCES)
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}
    if 'raw_ip' not in st.session_state:
        st.session_state.raw_ip = None
    if 'hashed_ip' not in st.session_state:
        st.session_state.hashed_ip = None
    if 'duplicate_flag' not in st.session_state:
        st.session_state.duplicate_flag = False
    if 'demographics_collected' not in st.session_state:
        st.session_state.demographics_collected = False

def show_consent_form():
    """Display the IRB consent form."""
    consent_path = get_consent_file_path()
    if consent_path.exists():
        consent_text = consent_path.read_text()
    else:
        consent_text = "IRB Consent text not found. Please ensure IRB_PROTOCOL_ID is set."

    st.markdown("### Informed Consent")
    st.info(f"Protocol ID: {IRB_PROTOCOL_ID}")
    st.markdown(consent_text)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree"):
            st.session_state.consent_given = True
            st.rerun()
    with col2:
        if st.button("I Do Not Agree"):
            st.info("Thank you for your time. You may leave this page.")
            st.stop()

def render_stimulus(condition_name: str):
    """Render the HTML stimulus file."""
    stimuli_path = get_project_root() / "code" / "stimuli" / f"{condition_name.lower().replace('-', '_')}.html"
    if not stimuli_path.exists():
        # Fallback for testing if file missing
        st.error(f"Stimulus file not found: {stimuli_path}")
        return

    with open(stimuli_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    st.markdown(f"### Stimulus: {condition_name}")
    st.components.v1.html(html_content, height=400, scrolling=True)

def collect_ratings(condition_name: str):
    """Collect Likert ratings for the current stimulus."""
    st.markdown(f"---")
    st.markdown(f"**Please rate the following for the content above:**")
    
    cred = st.slider(
        "Credibility (1 = Not Credible, 7 = Very Credible)",
        min_value=1, max_value=7, key=f"cred_{condition_name}"
    )
    prof = st.slider(
        "Professionalism (1 = Not Professional, 7 = Very Professional)",
        min_value=1, max_value=7, key=f"prof_{condition_name}"
    )
    
    # Store in session state
    st.session_state.ratings[condition_name] = {
        'credibility': cred,
        'professionalism': prof
    }

def show_demographics():
    """
    Render the demographic input form.
    Implements T023d_ui: Dropdown for Education, Number input for Age.
    """
    if st.session_state.demographics_collected:
        return

    st.markdown("### Demographics")
    st.markdown("Please provide the following information to complete the survey.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input(
            "Age (years)",
            min_value=18,
            max_value=120,
            step=1,
            key="age_input"
        )
    
    with col2:
        education_map = {
            1: "High School",
            2: "Bachelor's",
            3: "Master's",
            4: "PhD"
        }
        education_label = st.selectbox(
            "Education Level",
            options=list(education_map.values()),
            key="edu_input"
        )
        # Convert label back to integer code 1-4
        education_code = list(education_map.keys())[list(education_map.values()).index(education_label)]

    if st.button("Save Demographics"):
        if age is not None and education_code is not None:
            st.session_state.age = int(age)
            st.session_state.education_code = int(education_code)
            st.session_state.demographics_collected = True
            st.success("Demographics saved.")
            st.rerun()
        else:
            st.error("Please provide both Age and Education.")

def save_submission_logic():
    """
    Finalize and save the submission.
    Implements T023d: Write Age and Education to CSV.
    """
    # 1. Capture IP (Simulated via header or mock for local run)
    # In Streamlit, we can't easily get raw IP without a proxy, so we simulate or use a header if available
    raw_ip = st.query_params.get("ip", "127.0.0.1") # Mock fallback for local testing
    st.session_state.raw_ip = raw_ip
    
    # 2. Hash IP immediately
    hashed_ip_val = hash_ip(raw_ip)
    st.session_state.hashed_ip = hashed_ip_val
    
    # 3. Check duplicate
    # In a real app, we'd load the CSV here. For now, we assume no duplicates or read file.
    # Simplified check:
    existing_hashes = [] 
    try:
        import pandas as pd
        df = pd.read_csv(get_project_root() / "data" / "raw" / "submissions.csv")
        if 'hashed_ip' in df.columns:
            existing_hashes = df['hashed_ip'].tolist()
    except (FileNotFoundError, KeyError):
        pass
    
    is_dup = check_duplicate_ip(hashed_ip_val, existing_hashes)
    st.session_state.duplicate_flag = is_dup
    
    # 4. Collect Ratings
    # Flatten ratings
    all_ratings = {}
    for cond, data in st.session_state.ratings.items():
        all_ratings[f"cred_{cond}"] = data['credibility']
        all_ratings[f"prof_{cond}"] = data['professionalism']
    
    # 5. Get Demographics
    age = st.session_state.get('age', 0)
    edu_code = st.session_state.get('education_code', 0)
    
    if age == 0 or edu_code == 0:
        st.error("Demographics are missing. Please go back and fill them out.")
        return False

    # 6. Save
    device_info = {
        "user_agent": st.query_params.get("ua", "unknown"),
        "language": "en"
    }
    
    # We need a single condition for the row? The task implies one row per submission with all ratings?
    # Or one row per stimulus? 
    # T022 says "Append to submissions.csv". T018 says "8 ratings". 
    # Usually, this means one row per participant with columns for each rating.
    # Let's assume one row per participant containing all ratings.
    
    # Prepare ratings dict for helper (flattened)
    # Helper expects Dict[str, int] but we have multiple. 
    # Let's adjust helper to handle the specific structure or pass the flattened dict.
    # Actually, looking at T022, it says "record Participant ID, Stimulus Condition...". 
    # If we have 4 stimuli, we might have 4 rows or 1 row with 8 columns.
    # Given T023d asks to write Age/Edu to the CSV, and these are per-participant, 
    # it's most logical to have one row per participant.
    
    # Let's construct a row where ratings are embedded or we just pass the whole dict.
    # The helper `save_submission` expects a `ratings` dict. 
    # Let's pass the flattened dict of all ratings.
    
    save_submission(
        user_id=st.session_state.user_id,
        condition="ALL", # Or the sequence string
        ratings=all_ratings, # Contains all 8 ratings
        hashed_ip=hashed_ip_val,
        duplicate_flag=is_dup,
        age=age,
        education_code=edu_code,
        device_info=device_info
    )
    
    st.success("Thank you for your participation! Your data has been saved.")
    st.balloons()
    return True

def main():
    st.set_page_config(page_title="Credibility Survey", layout="wide")
    init_session_state()
    
    if not st.session_state.consent_given:
        show_consent_form()
        return
    
    st.header("Visual Aesthetics Survey")
    
    # Determine current step
    current_idx = st.session_state.current_stimulus_idx
    sequence = st.session_state.sequence
    
    if current_idx < len(sequence):
        condition = sequence[current_idx]
        render_stimulus(condition)
        collect_ratings(condition)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Previous"):
                if current_idx > 0:
                    st.session_state.current_stimulus_idx -= 1
                    st.rerun()
        with col2:
            if st.button("Next"):
                if current_idx < len(sequence) - 1:
                    st.session_state.current_stimulus_idx += 1
                    st.rerun()
                else:
                    # Last stimulus, go to demographics
                    st.session_state.current_stimulus_idx += 1
                    st.rerun()
    elif current_idx == len(sequence):
        # Demographics Step
        show_demographics()
        if st.session_state.demographics_collected:
            st.markdown("---")
            if st.button("Submit Survey"):
                if save_submission_logic():
                    # Reset state for next user (if local dev) or just stop
                    pass
    else:
        st.info("Survey complete.")

if __name__ == "__main__":
    main()