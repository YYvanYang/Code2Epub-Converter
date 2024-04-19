import os
import subprocess
import sys
import random
import time
import logging
import configparser
from weasyprint import HTML
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import concurrent.futures
from tqdm import tqdm

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get(self, section, option):
        return self.config.get(section, option)

class Logger:
    @staticmethod
    def setup_logging(level):
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

class GitManager:
    @staticmethod
    def clone_repo(repo_url, local_dir):
        if not os.path.exists('repo'):
            os.makedirs('repo')
        full_path = os.path.join('repo', local_dir)
        if os.path.exists(full_path):
            subprocess.run(['rm', '-rf', full_path], check=True)
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, full_path], check=True)
        return full_path

    @staticmethod
    def extract_repo_details(repo_url):
        parts = repo_url.split('/')
        repo_name = parts[-1].replace('.git', '')
        author = parts[-2] if len(parts) > 1 else 'Unknown Author'
        return repo_name, author

class FileManager:
    @staticmethod
    def process_file(file_path, full_repo_dir, chapters, code_css):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            logger.warning(f"Failed to read file: {file_path}. Error: {str(e)}. Skipping...")
            return chapters, code_css

        language = FileManager.detect_language(file_path)
        highlighted_code, css = SyntaxHighlighter.highlight_code(content, language)

        if not code_css:
            code_css = css

        relative_path = os.path.relpath(file_path, start=full_repo_dir)
        unique_file_name = FileManager.generate_unique_file_name(relative_path)
        chapter_title = relative_path.replace('_', ' ').replace('/', ' > ')

        chapter_content = f'<h1>{os.path.basename(file_path)}</h1><style>{css}</style>{highlighted_code}'
        chapter = epub.EpubHtml(title=chapter_title, file_name=unique_file_name + '.xhtml', lang='en')
        chapter.content = chapter_content
        chapters.append((chapter_title, chapter))

        return chapters, code_css

    @staticmethod
    def detect_language(file_path):
        if file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith(('.js', '.jsx')):
            return 'javascript'
        elif file_path.endswith(('.ts', '.tsx')):
            return 'typescript'
        elif file_path.endswith('.rs'):
            return 'rust'
        elif file_path.endswith('.md'):
            return 'markdown'
        return 'text'

    @staticmethod
    def generate_unique_file_name(relative_path):
        return "".join([c for c in relative_path.replace(os.path.sep, '_').replace(' ', '_') if c.isalpha() or c.isdigit() or c in ['_', '.']])

class SyntaxHighlighter:
    @staticmethod
    def highlight_code(code, language):
        try:
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(linenos='inline', cssclass="source", style='friendly')
            return highlight(code, lexer, formatter), formatter.get_style_defs('.source')
        except Exception as e:
            return code, ''

class DocumentGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.ensure_output_dir_exists()

    def create_pdf_with_toc(self, chapters, file_name):
        toc_html_list, chapters_html_list = self.generate_chapter_html(chapters)
        full_html_content = f"<html><body>{toc_html_list}{chapters_html_list}</body></html>"
        HTML(string=full_html_content).write_pdf(os.path.join(self.output_dir, file_name))

    @staticmethod
    def generate_chapter_html(chapters):
        toc_html = "<h1>Table of Contents</h1><ul>"
        chapters_html = ""
        for idx, (title, content) in enumerate(chapters):
            toc_html += f"<li><a href='#chapter{idx}'>{title}</a></li>"
            chapters_html += f"<h1 id='chapter{idx}'>{title}</h1>{content}"
        toc_html += "</ul>"
        return toc_html, chapters_html

    def create_epub(self, book, chapters, file_name):
        for _, chapter in chapters:
            book.add_item(chapter)
        book.spine = ['nav'] + [chapter for _, chapter in chapters]
        book.toc = [(epub.Section('Chapters'), [chapter for _, chapter in chapters])]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(os.path.join(self.output_dir, file_name), book, {})

    def ensure_output_dir_exists(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)


class EbookCreator:
    def __init__(self, config_manager, logger, git_manager, file_manager, doc_generator):
        self.config_manager = config_manager
        self.logger = logger
        self.git_manager = git_manager
        self.file_manager = file_manager
        self.doc_generator = doc_generator

    def run(self):
        repo_url = self.config_manager.get('github', 'repo_url')
        repo_name, author = self.git_manager.extract_repo_details(repo_url)
        local_dir = repo_name

        try:
            full_repo_dir = self.git_manager.clone_repo(repo_url, local_dir)
        except subprocess.CalledProcessError:
            self.logger.error("Failed to clone the repository. Exiting...")
            sys.exit(1)

        book = epub.EpubBook()
        book.set_identifier(str(random.randint(10000, 99999)))
        book.set_title(repo_name)
        book.set_language('en')
        book.add_author(author)

        chapters = []
        code_css = None

        supported_extensions = self.config_manager.get('output', 'supported_extensions').split(',')
        for root, dirs, files in os.walk(full_repo_dir):
            for file in tqdm(files, desc="Processing files", unit="file"):
                if file.endswith(tuple(supported_extensions)):
                    file_path = os.path.join(root, file)
                    chapters, code_css = self.file_manager.process_file(file_path, full_repo_dir, chapters, code_css)

        timestamp = time.strftime('%Y%m%d%H%M%S')
        file_name_format = self.config_manager.get('output', 'file_name_format')
        epub_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.epub'
        pdf_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.pdf'

        self.doc_generator.create_epub(book, chapters, epub_file_name)
        self.logger.info(f'Generated book: {epub_file_name}')
        self.logger.info(f'Local path: {os.path.abspath(os.path.join(self.doc_generator.output_dir, epub_file_name))}')

        pdf_file_path = os.path.join(self.doc_generator.output_dir, pdf_file_name)
        self.doc_generator.create_pdf_with_toc([(title, chapter.content) for title, chapter in chapters], pdf_file_path)
        self.logger.info(f'Generated PDF: {pdf_file_name}')
        self.logger.info(f'Local path: {os.path.abspath(pdf_file_path)}')

def main():
    config_manager = ConfigManager()
    logger = Logger.setup_logging(config_manager.get('logging', 'level'))
    git_manager = GitManager()
    file_manager = FileManager()
    output_dir = config_manager.get('output', 'output_dir')
    doc_generator = DocumentGenerator(output_dir)
    ebook_creator = EbookCreator(config_manager, logger, git_manager, file_manager, doc_generator)
    ebook_creator.run()

if __name__ == '__main__':
    main()
