import os
import subprocess
import random
import time
import logging
import fitz
import tempfile
import multiprocessing
import pickle
import importlib.util
from weasyprint import HTML
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from tqdm import tqdm
import argparse
import configparser
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeToEbook:
    def __init__(self, repo_url, output_dir, file_name_format, supported_extensions):
        self.repo_url = repo_url
        self.output_dir = output_dir
        self.file_name_format = file_name_format
        self.supported_extensions = supported_extensions
        self.repo_name, self.author = self.extract_repo_details()
        self.full_repo_dir = self.clone_github_repo()

    def extract_repo_details(self):
        parts = self.repo_url.split('/')
        repo_name = parts[-1].replace('.git', '')
        author = parts[-2] if len(parts) > 1 else 'Unknown Author'
        return repo_name, author

    def clone_github_repo(self):
        repo_dir = 'repo'
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)
        full_path = os.path.join(repo_dir, self.repo_name)
        if os.path.exists(full_path):
            subprocess.run(['rm', '-rf', full_path], check=True)
        try:
            subprocess.run(['git', 'clone', '--depth', '1', self.repo_url, full_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            logger.error(f"Error output: {e.output}")
            sys.exit(1)
        return full_path

    def process_files(self, file_list, chapters, code_css):
        with multiprocessing.Pool() as pool:
            results = []
            for file_path in file_list:
                result = pool.apply_async(process_file, (file_path, self.full_repo_dir, chapters, code_css))
                results.append(result)

            for result in results:
                chapters, code_css = result.get()

        return chapters, code_css

    def create_epub(self, chapters, code_css):
        book = epub.EpubBook()
        book.set_identifier(str(random.randint(10000, 99999)))
        book.set_title(self.repo_name)
        book.set_language('en')
        book.add_author(self.author)

        for title, chapter in chapters:
            book.add_item(chapter)

        book.spine = ['nav'] + [chapter for _, chapter in chapters]
        book.toc = [(epub.Section('Chapters'), [chapter for _, chapter in chapters])]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        timestamp = time.strftime('%Y%m%d%H%M%S')
        book_file_name = os.path.join(self.output_dir, self.file_name_format.format(repo_name=self.repo_name, timestamp=timestamp) + '.epub')

        try:
            epub.write_epub(book_file_name, book, {})
        except IOError as e:
            logger.error(f"Failed to write EPUB file: {e}")
            sys.exit(1)

        logger.info(f'Generated EPUB: {book_file_name}')
        logger.info(f'Local path: {os.path.abspath(book_file_name)}')

    def create_pdf(self, chapters):
        timestamp = time.strftime('%Y%m%d%H%M%S')
        pdf_file_name = os.path.join(self.output_dir, self.file_name_format.format(repo_name=self.repo_name, timestamp=timestamp) + '.pdf')

        try:
            create_pdf_with_toc([(title, chapter.content) for title, chapter in chapters], pdf_file_name)
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            sys.exit(1)

        logger.info(f'Generated PDF: {pdf_file_name}')
        logger.info(f'Local path: {os.path.abspath(pdf_file_name)}')

    def convert(self):
        self.load_plugins()

        last_conversion_time = self.load_last_conversion_time()

        file_list = []
        for root, dirs, files in os.walk(self.full_repo_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    if os.path.getmtime(file_path) > last_conversion_time:
                        file_list.append(file_path)

        if self.highlighter_plugin:
            chapters, code_css = self.highlighter_plugin.highlight_chapters(file_list)
        else:
            chapters, code_css = self.process_files(file_list, [], '')

        if self.ebook_format_plugin:
            self.ebook_format_plugin.create_ebook(chapters, code_css, self.repo_name, self.output_dir, self.file_name_format)
        else:
            self.create_epub(chapters, code_css)
            self.create_pdf(chapters)

        self.save_last_conversion_time()

    def load_last_conversion_time(self):
        timestamp_file = f'{self.repo_name}_last_conversion.pickle'
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'rb') as f:
                return pickle.load(f)
        return 0

    def save_last_conversion_time(self):
        timestamp_file = f'{self.repo_name}_last_conversion.pickle'
        with open(timestamp_file, 'wb') as f:
            pickle.dump(time.time(), f)

    def load_plugins(self):
        self.highlighter_plugin = None
        self.ebook_format_plugin = None

        # Load code highlighter plugin
        highlighter_plugin_path = os.path.join('plugins', 'highlighter.py')
        if os.path.exists(highlighter_plugin_path):
            spec = importlib.util.spec_from_file_location('highlighter', highlighter_plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.highlighter_plugin = module.CustomHighlighter()

        # Load ebook format plugin
        ebook_format_plugin_path = os.path.join('plugins', 'ebook_format.py')
        if os.path.exists(ebook_format_plugin_path):
            spec = importlib.util.spec_from_file_location('ebook_format', ebook_format_plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.ebook_format_plugin = module.CustomEbookFormat()

def process_file(file_path, full_repo_dir, chapters, code_css):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        logger.warning(f"Failed to read file: {file_path}. Skipping...")
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
    except Exception as e:
        logger.warning(f"Failed to highlight code for file: {file_path}. Using plain text.")
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

def create_pdf_with_toc(chapters, file_name):
    """
    Create a PDF file with a table of contents (TOC).

    Args:
        chapters (list[tuple[str, str]]): A list of tuples containing chapter titles and content.
        file_name (str): The output file name for the PDF.

    The function generates a PDF file in three steps:
    1. Generate an initial PDF without a table of contents.
    2. Analyze the initial PDF to determine page numbers for each chapter.
    3. Generate the final PDF with a table of contents using the page numbers.

    The table of contents is generated by extracting the chapter titles from the initial PDF
    and associating them with the corresponding page numbers.

    The function uses the WeasyPrint library to generate the PDF files.
    """
    # Step 1: Generate initial PDF without table of contents
    html_content = "<html><body>"
    for title, content in chapters:
        html_content += f'<h1 id="{title}">{title}</h1>{content}'
    html_content += "</body></html>"

    # Create a temporary file to store the initial PDF
    fd, initial_pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)

    try:
        HTML(string=html_content).write_pdf(initial_pdf_path)
    except Exception as e:
        logger.error(f"Failed to generate initial PDF: {e}")
        logger.error(f"Error details: {str(e)}")
        raise

    try:
        toc = extract_toc_from_pdf(initial_pdf_path, chapters)
    except Exception as e:
        logger.error(f"Failed to extract table of contents from PDF: {e}")
        raise
    finally:
        # Remove the temporary initial PDF file
        os.unlink(initial_pdf_path)

    # Generate HTML for the table of contents with clickable links
    toc_html = "<h1>Table of Contents</h1><ul>"
    for title, page_num in toc:
        toc_html += f'<li><a href="#page={page_num}">{title}</a></li>'
    toc_html += "</ul>"

    # Insert the table of contents HTML into the final HTML content
    final_html_content = html_content.replace("<body>", f"<body>{toc_html}")

    # Step 3: Generate the final PDF with table of contents
    try:
        HTML(string=final_html_content).write_pdf(file_name, stylesheets=[CSS(string='a { color: blue; text-decoration: none; }')])
    except Exception as e:
        logger.error(f"Failed to generate final PDF: {e}")
        logger.error(f"Error details: {str(e)}")
        raise

def extract_toc_from_pdf(pdf_path, chapters):
    """
    Extract the table of contents (TOC) from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.
        chapters (list[tuple[str, str]]): A list of tuples containing chapter titles and content.

    Returns:
        list[tuple[str, int]]: A list of tuples containing chapter titles and their corresponding page numbers.

    The function uses the PyMuPDF library to extract the table of contents information from the PDF file.
    It determines the page numbers by searching for the occurrence of each chapter title in the PDF.

    If any errors occur during the extraction of the table of contents, the function logs the error and re-raises the exception.
    """
    toc = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                for title, _ in chapters:
                    if title in text:
                        toc.append((title, page_num + 1))
                        break
    except fitz.FileDataError as e:
        logger.error(f"Failed to open PDF file: {e}")
        raise
    except fitz.FileNotFoundError as e:
        logger.error(f"PDF file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to extract table of contents from PDF: {e}")
        raise
    return toc

def highlight_code(code, language):
    """
    Apply syntax highlighting to the provided code using Pygments library.

    Args:
        code (str): The code to be highlighted.
        language (str): The programming language of the code.

    Returns:
        tuple[str, str]: A tuple containing the highlighted code and CSS styles.

    The function uses Pygments library to apply syntax highlighting to the code.
    It determines the appropriate lexer based on the provided language and uses
    the HtmlFormatter to generate the highlighted code and CSS styles.

    The highlighted code is returned as an HTML-formatted string, and the CSS styles
    are returned separately to be included in the generated EPUB or PDF file.
    """
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos='inline', cssclass="source", style='friendly')
    return highlight(code, lexer, formatter), formatter.get_style_defs('.source')

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Convert GitHub repository to EPUB and PDF')
    parser.add_argument('--repo-url', type=str, help='GitHub repository URL')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for generated files')
    parser.add_argument('--file-name-format', type=str, default='{repo_name}_{timestamp}', help='Format for output file names')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Logging level')

    # 解析命令行参数
    args = parser.parse_args()

    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini')

    # 优先使用命令行参数,如果未提供则使用配置文件中的值
    repo_url = args.repo_url or config.get('github', 'repo_url')
    output_dir = args.output_dir
    file_name_format = args.file_name_format or config.get('output', 'file_name_format')
    supported_extensions = config.get('output', 'supported_extensions').split(',')
    log_level = args.log_level or config.get('logging', 'level')

    # 配置日志级别
    logging.basicConfig(level=getattr(logging, log_level))

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Run tests using pytest
        import pytest
        pytest.main(['-v', 'tests'])
    else:
        converter = CodeToEbook(repo_url, output_dir, file_name_format, supported_extensions)
        converter.convert()

if __name__ == '__main__':
    main()
