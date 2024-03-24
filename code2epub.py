import os
import subprocess
import random
import time
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to ensure 'repo' directory exists
def ensure_repo_dir_exists():
    repo_dir = 'repo'
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)


# Function to clone a GitHub repository
def clone_github_repo(repo_url, local_dir):
    ensure_repo_dir_exists()  # Ensure the 'repo' directory exists
    full_path = os.path.join('repo', local_dir)
    if os.path.exists(full_path):
        subprocess.run(['rm', '-rf', full_path], check=True)
    subprocess.run(['git', 'clone', repo_url, full_path], check=True)
    return full_path

# Extract repository name and author from URL
def extract_repo_details(repo_url):
    parts = repo_url.split('/')
    repo_name = parts[-1].replace('.git', '')
    author = parts[-2] if len(parts) > 1 else 'Unknown Author'
    return repo_name, author

# Function to apply syntax highlighting to code
def highlight_code(code, language):
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos='inline', cssclass="source", style='friendly')
    return highlight(code, lexer, formatter), formatter.get_style_defs('.source')

# Main script
repo_url = os.getenv('REPO_URL')
repo_name, author = extract_repo_details(repo_url)
local_dir = repo_name

# Clone the GitHub repository
full_repo_dir = clone_github_repo(repo_url, local_dir)

# Create an EPUB book
book = epub.EpubBook()

# Set dynamic metadata
book.set_identifier(str(random.randint(10000, 99999)))
book.set_title(repo_name)
book.set_language('en')
book.add_author(author)

# Initialize a list to store chapters
chapters = []

# Initialize a variable to store CSS for code highlighting
code_css = None

# Walk through the directory and process files
for root, dirs, files in os.walk(full_repo_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.py', '.jsx', '.tsx', '.rs', '.md')):
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
                elif file.endswith('.rs'):
                    language = 'rust'
                elif file.endswith('.md'):
                    language = 'markdown'
                else:
                    language = 'text'
                
                highlighted_code, css = highlight_code(content, language)
                
                # Save the CSS for code highlighting
                if not code_css:
                    code_css = css

                # Generate a unique file name based on the file's relative path to the repo root
                relative_path = os.path.relpath(file_path, start=full_repo_dir)
                unique_file_name = relative_path.replace(os.path.sep, '_').replace(' ', '_')
                # Replace characters not allowed in file names
                unique_file_name = "".join([c for c in unique_file_name if c.isalpha() or c.isdigit() or c in ['_', '.']])
                
                # Use the relative path as the chapter title for the TOC
                chapter_title = relative_path.replace('_', ' ').replace('/', ' > ')
                        
                # Create a chapter
                chapter_content = f'<h1>{file}</h1><style>{css}</style>{highlighted_code}'
                chapter = epub.EpubHtml(title=chapter_title, file_name=unique_file_name + '.xhtml', lang='en')
                chapter.content = chapter_content
                book.add_item(chapter)
                        
                # Add the chapter to the chapters list
                chapters.append((chapter_title, chapter))

# Define the spine and TOC using the chapters list
book.spine = ['nav'] + [chapter for _, chapter in chapters]
book.toc = [(epub.Section('Chapters'), [chapter for _, chapter in chapters])]



# Add default NCX and cover
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Generate book file name with timestamp
timestamp = time.strftime('%Y%m%d%H%M%S')
book_file_name = f'{repo_name}_{timestamp}.epub'

# Write the EPUB file
epub.write_epub(book_file_name, book, {})

# Print the generated book name and local path
print(f'Generated book: {book_file_name}')
print(f'Local path: {os.path.abspath(book_file_name)}')
