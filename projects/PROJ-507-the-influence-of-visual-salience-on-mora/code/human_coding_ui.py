"""
Human Coding Interface for Visual Salience Study.

This Streamlit application allows ≥3 independent annotators to upload labels
for candidate images. It enforces the ≥3 annotator requirement and implements
majority vote logic for scenario resolution.

Output: data/processed/human_coding_annotations.csv
"""

import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import streamlit as st
import pandas as pd

# Add parent directory to path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import seed_everything
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
MIN_ANNOTATORS = 3
OUTPUT_FILE = Path("data/processed/human_coding_annotations.csv")
CANDIDATES_FILE = Path("data/processed/validated_candidates.csv")
EXISTING_ANNOTATIONS_FILE = Path("data/processed/human_coding_annotations.csv")

# Rating scale options (1-7 Likert scale for moral ambiguity)
RATING_OPTIONS = {
    1: "Very Low Ambiguity (Clearly Immoral)",
    2: "Low Ambiguity",
    3: "Somewhat Low Ambiguity",
    4: "Neutral / Moderate Ambiguity",
    5: "Somewhat High Ambiguity",
    6: "High Ambiguity",
    7: "Very High Ambiguity (Clearly Moral)"
}

def get_annotator_id() -> str:
    """
    Get or create a unique annotator ID for the current session.
    Uses a combination of IP hash (simulated) and timestamp to ensure uniqueness.
    """
    session_id = st.session_state.get("annotator_id")
    if not session_id:
        # Generate a unique ID based on timestamp and a random component
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_hash = hashlib.sha256(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
        session_id = f"ANN_{unique_hash}"
        st.session_state["annotator_id"] = session_id
        logger.info(f"New annotator session started: {session_id}")
    return session_id

def load_candidates() -> pd.DataFrame:
    """
    Load candidate scenarios from the validated_candidates.csv file.
    Returns a DataFrame with scenario_id, image_path, and metadata.
    """
    if not CANDIDATES_FILE.exists():
        st.error(f"Candidates file not found: {CANDIDATES_FILE}")
        logger.error(f"Candidates file not found: {CANDIDATES_FILE}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(CANDIDATES_FILE)
        logger.info(f"Loaded {len(df)} candidates from {CANDIDATES_FILE}")
        return df
    except Exception as e:
        st.error(f"Error loading candidates: {e}")
        logger.error(f"Error loading candidates: {e}")
        return pd.DataFrame()

def load_existing_annotations() -> pd.DataFrame:
    """
    Load existing annotations from the output file.
    Returns a DataFrame with scenario_id, annotator_id, rating.
    """
    if not OUTPUT_FILE.exists():
        return pd.DataFrame(columns=["scenario_id", "annotator_id", "rating", "timestamp"])

    try:
        df = pd.read_csv(OUTPUT_FILE)
        return df
    except Exception as e:
        logger.warning(f"Error loading existing annotations: {e}")
        return pd.DataFrame(columns=["scenario_id", "annotator_id", "rating", "timestamp"])

def save_annotation(scenario_id: str, annotator_id: str, rating: int, comments: str = "") -> bool:
    """
    Save a single annotation to the CSV file.
    Returns True if successful, False otherwise.
    """
    new_row = {
        "scenario_id": scenario_id,
        "annotator_id": annotator_id,
        "rating": rating,
        "timestamp": datetime.now().isoformat(),
        "comments": comments
    }

    try:
        # Load existing data
        existing_df = load_existing_annotations()

        # Check if this annotator has already rated this scenario
        if not existing_df.empty:
            already_rated = existing_df[
                (existing_df["scenario_id"] == scenario_id) &
                (existing_df["annotator_id"] == annotator_id)
            ]
            if not already_rated.empty:
                st.warning(f"You have already rated scenario {scenario_id}. Skipping save.")
                return False

        # Append new row
        new_df = pd.DataFrame([new_row])
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(OUTPUT_FILE, index=False)

        logger.info(f"Saved annotation: scenario={scenario_id}, annotator={annotator_id}, rating={rating}")
        return True

    except Exception as e:
        st.error(f"Error saving annotation: {e}")
        logger.error(f"Error saving annotation: {e}")
        return False

def check_annotator_requirement(existing_df: pd.DataFrame) -> Tuple[bool, int, Dict[int, int]]:
    """
    Check if the ≥3 annotator requirement is met for the current scenario.
    Returns (is_met, total_annotators, rating_distribution).
    """
    if existing_df.empty:
        return False, 0, {}

    total_annotators = existing_df["annotator_id"].nunique()
    rating_counts = existing_df["rating"].value_counts().to_dict()

    return total_annotators >= MIN_ANNOTATORS, total_annotators, rating_counts

def get_next_scenario_to_label(candidates_df: pd.DataFrame, existing_df: pd.DataFrame) -> Optional[str]:
    """
    Determine the next scenario that needs labeling.
    Priority:
    1. Scenarios with < MIN_ANNOTATORS ratings
    2. Scenarios with no ratings
    3. None if all scenarios are complete
    """
    if candidates_df.empty:
        return None

    # Get all scenario IDs
    all_scenarios = candidates_df["scenario_id"].tolist()

    if existing_df.empty:
        # No annotations yet, return first scenario
        return all_scenarios[0]

    # Count ratings per scenario
    rating_counts = existing_df.groupby("scenario_id").size()

    # Find scenarios that need more annotations
    for scenario_id in all_scenarios:
        count = rating_counts.get(scenario_id, 0)
        if count < MIN_ANNOTATORS:
            return scenario_id

    # All scenarios have at least MIN_ANNOTATORS ratings
    return None

def render_annotation_interface(
    scenario_id: str,
    image_path: str,
    existing_annotations: pd.DataFrame,
    current_annotator: str
) -> bool:
    """
    Render the Streamlit annotation interface for a specific scenario.
    Returns True if annotation was saved, False otherwise.
    """
    st.subheader(f"Annotating Scenario: {scenario_id}")

    # Display image
    if os.path.exists(image_path):
        st.image(image_path, caption=f"Scenario {scenario_id}", use_container_width=True)
    else:
        st.warning(f"Image not found: {image_path}")
        st.info(f"Please rate based on the scenario description if image is missing.")

    # Show existing annotations for this scenario
    st.markdown("### Previous Annotations")
    scenario_annotations = existing_annotations[existing_annotations["scenario_id"] == scenario_id]

    if not scenario_annotations.empty:
        st.write(f"Total annotations: {len(scenario_annotations)}")
        st.write("Rating distribution:")
        rating_dist = scenario_annotations["rating"].value_counts().sort_index()
        st.bar_chart(rating_dist)

        # Show individual ratings (anonymized)
        st.write("Individual ratings:")
        for idx, row in scenario_annotations.iterrows():
            annot_id = row["annotator_id"]
            rating = row["rating"]
            comments = row.get("comments", "")
            st.text(f"Annotator {annot_id}: {rating}/7 - {comments}")
    else:
        st.info("No previous annotations for this scenario.")

    # Annotation form
    st.markdown("### Your Annotation")

    rating = st.selectbox(
        "Rate the moral ambiguity of this scenario:",
        options=list(RATING_OPTIONS.keys()),
        format_func=lambda x: RATING_OPTIONS[x],
        key=f"rating_{scenario_id}"
    )

    comments = st.text_area(
        "Comments (optional):",
        help="Briefly explain your rating if desired.",
        key=f"comments_{scenario_id}"
    )

    col1, col2 = st.columns(2)
    with col1:
        submit_btn = st.button("Submit Annotation", type="primary")
    with col2:
        skip_btn = st.button("Skip Scenario")

    if submit_btn:
        success = save_annotation(scenario_id, current_annotator, rating, comments)
        if success:
            st.success("Annotation saved successfully!")
            return True
        else:
            st.error("Failed to save annotation.")

    if skip_btn:
        st.info("Skipped this scenario.")
        return False

    return False

def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="Human Coding Interface",
        page_icon="📝",
        layout="wide"
    )

    st.title("📝 Human Coding Interface for Visual Salience Study")
    st.markdown("""
    This interface allows independent annotators to label morally ambiguous scenarios.
    **Requirements:**
    - Each scenario must be rated by at least **3 independent annotators**.
    - Ratings are on a 1-7 scale (1 = Clearly Immoral, 7 = Clearly Moral).
    - Scenarios without majority agreement will be excluded from analysis.
    """)

    # Initialize annotator ID
    annotator_id = get_annotator_id()
    st.sidebar.markdown(f"**Current Annotator:** `{annotator_id}`")

    # Load data
    candidates_df = load_candidates()
    existing_df = load_existing_annotations()

    if candidates_df.empty:
        st.error("No candidates found. Please run the data preparation pipeline first.")
        st.stop()

    # Get next scenario to label
    next_scenario_id = get_next_scenario_to_label(candidates_df, existing_df)

    if next_scenario_id is None:
        st.success("🎉 All scenarios have been rated by at least 3 annotators!")
        st.info("Please check with the study coordinator for next steps.")

        # Show summary statistics
        st.markdown("### Summary Statistics")
        st.write(f"Total scenarios: {len(candidates_df)}")
        st.write(f"Total annotations: {len(existing_df)}")
        st.write(f"Unique annotators: {existing_df['annotator_id'].nunique()}")

        # Show completion status
        completion_df = candidates_df.merge(
            existing_df.groupby("scenario_id").size().reset_index(name="annotation_count"),
            on="scenario_id",
            how="left"
        )
        completion_df["annotation_count"] = completion_df["annotation_count"].fillna(0)
        st.write("Completion status by scenario:")
        st.dataframe(completion_df)

        return

    # Get scenario details
    scenario_row = candidates_df[candidates_df["scenario_id"] == next_scenario_id].iloc[0]
    image_path = scenario_row.get("image_path", "")

    # Check if current annotator has already rated this scenario
    if not existing_df.empty:
        already_rated = existing_df[
            (existing_df["scenario_id"] == next_scenario_id) &
            (existing_df["annotator_id"] == annotator_id)
        ]
        if not already_rated.empty:
            st.info(f"You have already rated scenario {next_scenario_id}. Moving to next scenario.")
            # Force re-evaluation to find next unlabelled scenario
            st.rerun()

    # Render annotation interface
    st.markdown(f"### Current Task: Scenario {next_scenario_id}")
    st.markdown(f"Image Path: `{image_path}`")

    # Check requirement status for this scenario
    is_met, total, rating_dist = check_annotator_requirement(
        existing_df[existing_df["scenario_id"] == next_scenario_id]
    )

    if is_met:
        st.warning(f"⚠️ This scenario already has {total} annotations (≥{MIN_ANNOTATORS}).")
        st.info("However, you can still contribute if needed for verification.")

    st.markdown("---")

    # Render the annotation interface
    annotation_saved = render_annotation_interface(
        scenario_id=next_scenario_id,
        image_path=image_path,
        existing_annotations=existing_df,
        current_annotator=annotator_id
    )

    if annotation_saved:
        st.success("Moving to next scenario...")
        time.sleep(1)
        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    **Notes:**
    - Your rating is anonymous and will be combined with others.
    - If there is no majority vote (e.g., 1-1-1), the scenario will be excluded.
    - Please provide honest and thoughtful ratings.
    """)

if __name__ == "__main__":
    main()
