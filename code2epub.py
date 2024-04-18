import os
import subprocess
import sys
import random
import time
import logging
import fitz
import tempfile
import configparser
from weasyprint import HTML
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import concurrent.futures
from tqdm import tqdm

# Read the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Configure logging level from the config file
logging_level = config.get('logging', 'level')
logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_output_dir_exists(output_dir: str) -> None:
    """
    Ensure the output directory exists.

    Args:
        output_dir (str): The output directory path.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def clone_github_repo(repo_url: str, local_dir: str) -> str:
    """
    Clone a GitHub repository.

    Args:
        repo_url (str): The URL of the GitHub repository.
        local_dir (str): The local directory to clone the repository into.

    Returns:
        str: The full path of the cloned repository.
    """
    ensure_output_dir_exists('repo')
    full_path = os.path.join('repo', local_dir)
    if os.path.exists(full_path):
        subprocess.run(['rm', '-rf', full_path], check=True)
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, full_path], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {repo_url}. Error: {str(e)}")
        sys.exit(1)
    return full_path

def extract_repo_details(repo_url: str) -> tuple[str, str]:
    """
    Extract repository name and author from the repository URL.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        tuple[str, str]: A tuple containing the repository name and author.
    """
    parts = repo_url.split('/')
    repo_name = parts[-1].replace('.git', '')
    author = parts[-2] if len(parts) > 1 else 'Unknown Author'
    return repo_name, author

def create_pdf_with_toc(chapters: list[tuple[str, str]], file_name: str) -> None:
    """
    Create a PDF file with a table of contents, using multithreading to process chapters.

    Args:
        chapters (list[tuple[str, str]]): A list of tuples containing chapter titles and content.
        file_name (str): The output file name for the PDF.
    """
    # Helper function to generate HTML for each chapter
    def generate_html(index, title, content):
        toc_entry = f"<li><a href='#chapter{index}'>{title}</a></li>"
        chapter_html = f"<h1 id='chapter{index}'>{title}</h1>{content}"
        return toc_entry, chapter_html

    # Initialize progress bar
    pbar = tqdm(total=len(chapters), desc="Generating PDF", unit="chapter")

    # Prepare to collect chapter HTML in order
    toc_html_list = []
    chapters_html_list = []

    # Use ThreadPoolExecutor to process chapters in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map each chapter to the executor
        future_to_chapter = {executor.submit(generate_html, idx, title, content): (idx, title)
                             for idx, (title, content) in enumerate(chapters)}
        for future in concurrent.futures.as_completed(future_to_chapter):
            idx, title = future_to_chapter[future]
            try:
                toc_entry, chapter_html = future.result()
                toc_html_list.append((idx, toc_entry))
                chapters_html_list.append((idx, chapter_html))
                pbar.update(1)
            except Exception as e:
                logger.error(f"Error processing chapter {title}: {str(e)}")

    # Sort chapters by index to maintain order
    toc_html_list.sort()
    chapters_html_list.sort()
    toc_html = "<h1>Table of Contents</h1><ul>" + "".join([entry for _, entry in toc_html_list]) + "</ul>"
    chapters_html = "".join([html for _, html in chapters_html_list])
    full_html_content = f"<html><body>{toc_html}{chapters_html}</body></html>"

    # Close progress bar
    pbar.close()

    # Generate PDF from full HTML content
    try:
        HTML(string=full_html_content).write_pdf(file_name)
        logger.info(f"PDF generated successfully at {file_name}")
    except Exception as e:
        logger.error(f"Failed to generate final PDF: {str(e)}")
        sys.exit(1)

def highlight_code(code: str, language: str) -> tuple[str, str]:
    """
    Apply syntax highlighting to code.

    Args:
        code (str): The code to be highlighted.
        language (str): The programming language of the code.

    Returns:
        tuple[str, str]: A tuple containing the highlighted code and CSS styles.
    """
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos='inline', cssclass="source", style='friendly')
    return highlight(code, lexer, formatter), formatter.get_style_defs('.source')

def process_file(file_path: str, full_repo_dir: str, chapters: list[tuple[str, epub.EpubHtml]], code_css: str) -> tuple[list[tuple[str, epub.EpubHtml]], str]:
    """
    Process a single file and add it as a chapter to the list of chapters.

    Args:
        file_path (str): The path to the file to process.
        full_repo_dir (str): The full path to the cloned repository directory.
        chapters (list[tuple[str, epub.EpubHtml]]): The list of chapters to append the processed file to.
        code_css (str): The CSS styles for code highlighting.

    Returns:
        tuple[list[tuple[str, epub.EpubHtml]], str]: A tuple containing the updated list of chapters and the updated code_css.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        logger.warning(f"Failed to read file: {file_path}. Error: {str(e)}. Skipping...")
        return chapters, code_css

    # Determine the programming language
    if file_path.endswith('.py'):
        language = 'python'
    elif file_path.endswith(('.js', '.jsx')):
        language = 'javascript'
    elif file_path.endswith(('.ts', '.tsx')):
        language = 'typescript'
    elif file_path.endswith('.rs'):
        language = 'rust'
    elif file_path.endswith('.md'):
        language = 'markdown'
    else:
        language = 'text'

    try:
        highlighted_code, css = highlight_code(content, language)
    except ValueError as e:
        logger.warning(f"Failed to highlight code for file: {file_path}. Error: {str(e)}. Using plain text.")
        highlighted_code, css = content, ''
    except Exception as e:
        logger.warning(f"Failed to highlight code for file: {file_path}. Error: {str(e)}. Using plain text.")
        highlighted_code, css = content, ''

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
    chapter_content = f'<h1>{os.path.basename(file_path)}</h1><style>{css}</style>{highlighted_code}'
    chapter = epub.EpubHtml(title=chapter_title, file_name=unique_file_name + '.xhtml', lang='en')
    chapter.content = chapter_content

    # Add the chapter to the chapters list
    chapters.append((chapter_title, chapter))

    return chapters, code_css

def main():
    """
    Main function to execute the code-to-ebook conversion.
    """
    repo_url = config.get('github', 'repo_url')
    repo_name, author = extract_repo_details(repo_url)
    local_dir = repo_name

    # Clone the GitHub repository
    try:
        full_repo_dir = clone_github_repo(repo_url, local_dir)
    except subprocess.CalledProcessError:
        logger.error("Failed to clone the repository. Exiting...")
        sys.exit(1)

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
    supported_extensions = config.get('output', 'supported_extensions').split(',')
    for root, dirs, files in os.walk(full_repo_dir):
        for file in tqdm(files, desc="Processing files", unit="file"):
            if file.endswith(tuple(supported_extensions)):
                file_path = os.path.join(root, file)
                chapters, code_css = process_file(file_path, full_repo_dir, chapters, code_css)

    # Add the chapters to the book
    for _, chapter in chapters:
        book.add_item(chapter)

    # Define the spine and TOC
    book.spine = ['nav'] + [chapter for _, chapter in chapters]
    book.toc = [(epub.Section('Chapters'), [chapter for _, chapter in chapters])]

    # Add default NCX and cover
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Generate book file name with timestamp
    timestamp = time.strftime('%Y%m%d%H%M%S')
    file_name_format = config.get('output', 'file_name_format')
    book_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.epub'
    pdf_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.pdf'

    # Create the output directory if it doesn't exist
    output_dir = config.get('output', 'output_dir')
    ensure_output_dir_exists(output_dir)

    # Write the EPUB file
    epub_file_path = os.path.join(output_dir, book_file_name)
    try:
        epub.write_epub(epub_file_path, book, {})
    except IOError as e:
        logger.error(f"Failed to write EPUB file: {str(e)}")
        sys.exit(1)

    # Print the generated book name and local path
    logger.info(f'Generated book: {book_file_name}')
    logger.info(f'Local path: {os.path.abspath(epub_file_path)}')

    # Call the function to create a PDF with WeasyPrint
    pdf_file_path = os.path.join(output_dir, pdf_file_name)
    try:
        create_pdf_with_toc([(title, chapter.content) for title, chapter in chapters], pdf_file_path)
    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}")
        sys.exit(1)

    logger.info(f'Generated PDF: {pdf_file_name}')
    logger.info(f'Local path: {os.path.abspath(pdf_file_path)}')

if __name__ == '__main__':
    main()
