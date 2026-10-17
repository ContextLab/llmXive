import pathlib
from llmxive_toolkit import paths

def setup():
    """Create the project directory hierarchy as specified in T001."""
    # These paths.xxx calls create the directories automatically
    paths.code("data")
    paths.code("analysis")
    paths.code("viz")
    paths.code("tests")
    paths.data("raw")
    paths.data("processed")
    paths.results()
    paths.figures()
    
    # Create the specs directory for the quickstart guide
    spec_dir = pathlib.Path("specs/001-quantifying-correlations-between-solar-w")
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    print("Project directory hierarchy created successfully.")

if __name__ == "__main__":
    setup()
