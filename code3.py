import os
import subprocess
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# Function to clone a GitHub repository
def clone_github_repo(repo_url, local_dir):
    if os.path.exists(local_dir):
        subprocess.run(['rm', '-rf', local_dir], check=True)
    subprocess.run(['git', 'clone', repo_url, local_dir], check=True)

# Function to apply syntax highlighting to code
def highlight_code(code, language):
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(code, lexer, formatter), formatter.get_style_defs('.source')

# Clone the GitHub repository
repo_url = 'https://github.com/YYvanYang/ai-gateway-openai-wrapper.git'
local_dir = 'repo'
clone_github_repo(repo_url, local_dir)

# Create an EPUB book
book = epub.EpubBook()

# Set metadata
book.set_identifier('id123456')
book.set_title('Your Book Title')
book.set_language('en')
book.add_author('Author Name')

# Initialize a list to store chapters
chapters = []

# Initialize a variable to store CSS for code highlighting
code_css = None

# Walk through the directory and process files
for root, dirs, files in os.walk(local_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.py', '.jsx', '.tsx')):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Determine the programming language
                if file.endswith('.py'):
                    language = 'python'
                elif file.endswith(('.js', '.jsx')):
                    language = 'javascript'
                elif file.endswith(('.ts', '.tsx')):
                    language = 'typescript'
                else:
                    language = 'text'
                
                highlighted_code, css = highlight_code(content, language)
                
                # Save the CSS for code highlighting
                if not code_css:
                    code_css = css
                
                # Create a chapter
                chapter = epub.EpubHtml(title=file, file_name=file + '.xhtml', lang='en')
                chapter.content = f'<h1>{file}</h1>{highlighted_code}'
                book.add_item(chapter)
                
                # Add the chapter to the chapters list
                chapters.append(chapter)

# Add the CSS for code highlighting to the book
style_code = epub.EpubItem(uid="style_code", file_name="style/code.css", media_type="text/css", content=code_css)
book.add_item(style_code)

# Define the spine and TOC using the chapters list
book.spine = ['nav'] + chapters
book.toc = [(epub.Section('Chapters'), chapters)]

# Add default NCX and cover
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Write the EPUB file
epub.write_epub('your_book.epub', book, {})
