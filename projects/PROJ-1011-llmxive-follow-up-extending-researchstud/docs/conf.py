"""
Sphinx configuration for llmXive API documentation.
"""
import os
import sys
from datetime import datetime

# Add the project root to the path so we can import code modules
# The code directory is at the project root level relative to docs/
sys.path.insert(0, os.path.abspath('..'))

project = 'llmXive'
copyright = f'{datetime.now().year}, llmXive Research Team'
author = 'llmXive Team'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx_autodoc_typehints',
    'm2r2'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output configuration
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'llmXivedoc'

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'show-inheritance': True,
    'special-members': '__init__',
}
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# Napoleon (Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = False
