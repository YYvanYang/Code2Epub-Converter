import os
from code2epub import extract_repo_details, highlight_code

def test_extract_repo_details():
    # Test case 1: GitHub repository URL with username and repo name
    repo_url = "https://github.com/username/repo"
    repo_name, author = extract_repo_details(repo_url)
    assert repo_name == "repo"
    assert author == "username"

    # Test case 2: GitHub repository URL without username
    repo_url = "https://github.com/repo"
    repo_name, author = extract_repo_details(repo_url)
    assert repo_name == "repo"
    assert author == "Unknown Author"

def test_highlight_code():
    # Test case 1: Python code highlighting
    code = "def hello():\n    print('Hello, World!')"
    language = "python"
    highlighted_code, css = highlight_code(code, language)
    assert "<pre>" in highlighted_code
    assert "def" in highlighted_code
    assert "print" in highlighted_code
    assert ".highlight" in css

    # Test case 2: JavaScript code highlighting
    code = "function hello() {\n    console.log('Hello, World!');\n}"
    language = "javascript"
    highlighted_code, css = highlight_code(code, language)
    assert "<pre>" in highlighted_code
    assert "function" in highlighted_code
    assert "console" in highlighted_code
    assert ".highlight" in css
