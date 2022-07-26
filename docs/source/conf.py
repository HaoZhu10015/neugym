import os
import sys
sys.path.insert(0, os.path.abspath("../.."))

import neugym as ng

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'NeuGym'
copyright = '2022, NeuGym Developers'
# author = 'Hao Zhu'
version = ng.__version__
release = ng.__version__.replace("_", "")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "numpydoc",
    "texext"
]

templates_path = ['_templates']
exclude_patterns = []

suppress_warnings = ["ref.citation", "ref.footnote"]

autosummary_generate = True
add_module_names = False
numpydoc_show_class_members = False

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_css_files = ["custom.css"]
html_logo = "_static/neugym_banner.svg"

html_theme_options = {
    "collapse_navigation": True,
    "navigation_depth": 3,
    "show_prev_next": False,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/HaoZhu10015/neugym",
            "icon": "fab fa-github-square",
        },
    ],
}


# -- Options for LaTeX output -------------------------------------------------

# Use a latex engine that allows for unicode characters in docstrings
latex_engine = "xelatex"
latex_paper_size = "a4"

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
    (
        "reference/index",
        "neugym_reference.tex",
        "NeuGym Reference",
        "NeuGym Development Team",
        "manual",
        1,
    )
]

latex_appendices = [
    "install",
    "tutorial"
]
