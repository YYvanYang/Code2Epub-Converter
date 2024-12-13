import os
import subprocess
import sys
import random
import time
import logging
import configparser
import asyncio
import aiofiles
from weasyprint import HTML
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import concurrent.futures
from tqdm import tqdm
from lxml import etree
import io
import pdfkit
import magic
import chardet
import pathspec
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

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
        try:
            os.makedirs('repo', exist_ok=True)
            full_path = os.path.join('repo', local_dir)
            if os.path.exists(full_path):
                # 尝试先更新已存在的仓库
                try:
                    subprocess.run(['git', '-C', full_path, 'pull'], check=True)
                    return full_path
                except subprocess.CalledProcessError:
                    # 如果更新失败,则删除重新克隆
                    subprocess.run(['rm', '-rf', full_path], check=True)
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, full_path], check=True)
            return full_path
        except Exception as e:
            raise RuntimeError(f"Git操作失败: {str(e)}")

    @staticmethod
    def extract_repo_details(repo_url):
        parts = repo_url.split('/')
        repo_name = parts[-1].replace('.git', '')
        author = parts[-2] if len(parts) > 1 else 'Unknown Author'
        return repo_name, author

class FileManager:
    def __init__(self, logger, supported_extensions, max_file_size_mb=10):
        self.logger = logger
        self.supported_extensions = supported_extensions
        self.max_file_size = max_file_size_mb * 1024 * 1024
        try:
            self.magic = magic.Magic(mime=True)
            self.use_magic = True
        except Exception as e:
            self.logger.warning(f"libmagic 初始化失败，将使用文件扩展名判断: {str(e)}")
            self.use_magic = False

    def _is_text_file(self, file_path):
        if self.use_magic:
            try:
                mime_type = self.magic.from_file(file_path)
                return mime_type.startswith('text/')
            except Exception:
                self.logger.warning(f"libmagic 检测失败，降级使用文件扩展名判断")
                return self._is_text_file_by_extension(file_path)
        return self._is_text_file_by_extension(file_path)

    def _is_text_file_by_extension(self, file_path):
        return any(file_path.endswith(ext) for ext in self.supported_extensions)

    def _read_file(self, file_path):
        # 检查文件大小
        if os.path.getsize(file_path) > self.max_file_size:
            self.logger.warning(f"文件过大(>{self.max_file_size/1024/1024}MB): {file_path}")
            return None
            
        # 检查文件类型
        if not self._is_text_file(file_path):
            self.logger.warning(f"不支持的文件类型: {file_path}")
            return None

        # 使用chardet检测编码
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                return raw_data.decode(encoding)
        except Exception as e:
            self.logger.error(f"文件读取失败: {file_path}, {str(e)}")
            return None

    def process_file(self, file_path, full_repo_dir):
        content = self._read_file(file_path)
        if content is None:
            return None

        language = self._detect_language(file_path)
        highlighted_code, css = SyntaxHighlighter.highlight_code(content, language)

        relative_path = os.path.relpath(file_path, start=full_repo_dir)
        unique_file_name = self._generate_unique_file_name(relative_path)
        chapter_title = relative_path.replace('_', ' ').replace('/', ' > ')

        chapter_content = f'<h1>{os.path.basename(file_path)}</h1><style>{css}</style>{highlighted_code}'
        chapter = epub.EpubHtml(title=chapter_title, file_name=unique_file_name + '.xhtml', lang='en')
        chapter.content = chapter_content

        return chapter_title, chapter, css

    @staticmethod
    def _detect_language(file_path):
        extension = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.rs': 'rust',
            '.md': 'markdown'
        }
        return language_map.get(extension, 'text')

    @staticmethod
    def _generate_unique_file_name(relative_path):
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
        os.makedirs(self.output_dir, exist_ok=True)
        # 配置pdfkit选项
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '2cm',
            'margin-right': '2cm',
            'margin-bottom': '2cm',
            'margin-left': '2cm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }

    async def create_pdf_with_toc(self, chapters, file_name, chunk_size=50):
        self.logger.info("开始生成PDF...")
        
        # 基础CSS样式
        css = """
        <style>
            body { font-family: Arial, sans-serif; }
            pre, code { 
                white-space: pre-wrap;
                word-wrap: break-word;
                font-size: 14px;
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
            }
            h1 { 
                page-break-before: always;
                color: #333;
                border-bottom: 1px solid #ccc;
                padding-bottom: 10px;
            }
            .toc-item { 
                margin: 5px 0;
                color: #0066cc;
            }
            .source { max-width: 100%; }
            @page { margin: 2cm; }
        </style>
        """

        # 创建HTML结构
        root = etree.Element("html")
        head = etree.SubElement(root, "head")
        head.append(etree.XML(css))
        body = etree.SubElement(root, "body")

        # 生成目录
        toc = etree.SubElement(body, "h1")
        toc.text = "目录"
        toc_list = etree.SubElement(body, "div", style="margin-left: 20px;")

        self.logger.info("正在处理章节...")
        
        # 分块处理章节
        for i in range(0, len(chapters), chunk_size):
            chunk = chapters[i:i+chunk_size]
            await self._process_chunk(chunk, body, toc_list, i)
            self.logger.info(f"已处理 {min(i + chunk_size, len(chapters))}/{len(chapters)} 个章节")

        self.logger.info("正在生成PDF文件...")
        
        # 生成PDF
        html_content = etree.tostring(root, pretty_print=True, encoding='unicode')
        pdf_bytes = await self._generate_pdf(html_content)

        # 写入文件
        async with aiofiles.open(file_name, 'wb') as f:
            await f.write(pdf_bytes)
            self.logger.info(f"PDF文件已保存: {file_name}")

    async def _process_chunk(self, chunk, body, toc_list, start_index):
        for idx, (title, content) in enumerate(chunk, start=start_index):
            # 添加到目录
            toc_item = etree.SubElement(toc_list, "div", Class="toc-item")
            toc_link = etree.SubElement(toc_item, "a", href=f'#chapter{idx}')
            toc_link.text = title

            # 添加章节内容
            chapter = etree.SubElement(body, "h1", id=f'chapter{idx}')
            chapter.text = title
            try:
                chapter_content = etree.fromstring(f"<div>{content}</div>")
                body.append(chapter_content)
            except etree.XMLSyntaxError as e:
                self.logger.warning(f"解析章节内容失败: {title}, 错误: {str(e)}")
                # 使用纯文本方式添加
                content_div = etree.SubElement(body, "div")
                content_div.text = content

    async def _generate_pdf(self, html_content):
        loop = asyncio.get_event_loop()
        self.logger.info("开始渲染PDF...")
        try:
            # 使用pdfkit替代WeasyPrint
            return await loop.run_in_executor(
                None,
                lambda: pdfkit.from_string(
                    html_content,
                    False,  # 输出到bytes而不是文件
                    options=self.pdf_options
                )
            )
        except Exception as e:
            self.logger.error(f"PDF渲染失败: {str(e)}")
            raise

    def create_epub(self, book, chapters, file_name):
        for _, chapter in chapters:
            book.add_item(chapter)
        book.spine = ['nav'] + [chapter for _, chapter in chapters]
        book.toc = [(epub.Section('Chapters'), [chapter for _, chapter in chapters])]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(file_name, book, {})

class EbookCreator:
    def __init__(self, config_manager, logger, git_manager, file_manager, doc_generator):
        self.config_manager = config_manager
        self.logger = logger
        self.git_manager = git_manager
        self.file_manager = file_manager
        self.doc_generator = doc_generator
        self.supported_extensions = file_manager.supported_extensions
        self.doc_generator.logger = logger

    async def run(self, progress_callback=None):
        repo_url = self.config_manager.get('github', 'repo_url')
        repo_name, author = self.git_manager.extract_repo_details(repo_url)
        local_dir = repo_name

        if progress_callback:
            progress_callback("正在克隆仓库...", 0)

        try:
            full_repo_dir = self.git_manager.clone_repo(repo_url, local_dir)
        except Exception as e:
            self.logger.error(f"克隆仓库失败: {str(e)}")
            return False

        # 创建电子书对象
        book = epub.EpubBook()
        book.set_identifier(str(random.randint(10000, 99999)))
        book.set_title(repo_name)
        book.set_language('en')
        book.add_author(author)

        chapters = []
        code_css = None

        # 获取要处理的文件列表
        files_to_process = self._get_files_to_process(full_repo_dir, self.supported_extensions)
        total_files = len(files_to_process)
        
        # 使用进度条处理文件
        with tqdm(total=total_files, desc="处理文件") as pbar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_file = {
                    executor.submit(
                        self.file_manager.process_file, 
                        file_path, 
                        full_repo_dir
                    ): file_path for file_path in files_to_process
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    if progress_callback:
                        current = pbar.n + 1
                        progress_callback(f"处理文件 {current}/{total_files}", current/total_files)
                    
                    result = future.result()
                    if result:
                        chapter_title, chapter, css = result
                        chapters.append((chapter_title, chapter))
                        if not code_css:
                            code_css = css
                    pbar.update(1)

        if not chapters:
            self.logger.error("没有找到可处理的文件")
            return False

        # 生成输出文件名
        timestamp = time.strftime('%Y%m%d%H%M%S')
        file_name_format = self.config_manager.get('output', 'file_name_format')
        epub_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.epub'
        pdf_file_name = file_name_format.format(repo_name=repo_name, timestamp=timestamp) + '.pdf'

        epub_full_path = os.path.join(self.doc_generator.output_dir, epub_file_name)
        pdf_full_path = os.path.join(self.doc_generator.output_dir, pdf_file_name)

        # 生成EPUB
        if progress_callback:
            progress_callback("生成EPUB文件...", 0.9)
        
        self.doc_generator.create_epub(book, chapters, epub_full_path)
        self.logger.info(f'生成EPUB: {epub_full_path}')
        self.logger.info(f'本地路径: {os.path.abspath(epub_full_path)}')

        # 生成PDF
        if progress_callback:
            progress_callback("生成PDF文件...", 0.95)
        
        await self.doc_generator.create_pdf_with_toc(
            [(title, chapter.content) for title, chapter in chapters], 
            pdf_full_path
        )
        self.logger.info(f'生成PDF: {pdf_full_path}')
        self.logger.info(f'本地路径: {os.path.abspath(pdf_full_path)}')

        if progress_callback:
            progress_callback("处理完成", 1.0)

        return True

    def _get_files_to_process(self, full_repo_dir, supported_extensions):
        spec = pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern,
            [f"**/*{ext}" for ext in supported_extensions]
        )
        
        matches = spec.match_tree(full_repo_dir)
        return [os.path.join(full_repo_dir, match) for match in matches]

app = typer.Typer()
console = Console()

@app.command()
def main(
    repo_url: str = typer.Option(None, "--repo-url", "-r", help="GitHub仓库URL"),
    output_dir: str = typer.Option("output", "--output-dir", "-o", help="输出目录"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="日志级别")
):
    """
    将GitHub代码仓库转换为电子书
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("正在处理...", total=None)
        
        # 初始化组件
        config_manager = ConfigManager()
        if repo_url:
            config_manager.config.set('github', 'repo_url', repo_url)
        if output_dir:
            config_manager.config.set('output', 'output_dir', output_dir)
        
        logger = Logger.setup_logging(log_level)
        git_manager = GitManager()
        supported_extensions = config_manager.get('output', 'supported_extensions').split(',')
        file_manager = FileManager(logger, supported_extensions)
        doc_generator = DocumentGenerator(config_manager.get('output', 'output_dir'))
        
        # 创建电子书生成器
        ebook_creator = EbookCreator(
            config_manager,
            logger,
            git_manager,
            file_manager,
            doc_generator
        )
        
        def update_progress(description: str, completed: float):
            progress.update(task, description=description)
        
        # 运行转换过程
        try:
            # 使用事件循环运行异步函数
            result = asyncio.run(ebook_creator.run(progress_callback=update_progress))
            if result:
                console.print("[green]转换完成！[/green]")
            else:
                console.print("[red]转换失败！[/red]")
        except Exception as e:
            console.print(f"[red]发生错误: {str(e)}[/red]")
            raise typer.Exit(1)

if __name__ == '__main__':
    app()
