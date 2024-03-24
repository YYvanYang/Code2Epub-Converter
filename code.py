import os
import shutil
from git import Repo
from ebooklib import epub
from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

# 克隆代码仓库
repo_url = 'https://github.com/YYvanYang/ai-gateway-openai-wrapper.git'
repo_dir = './repo'

# 如果repo_dir已存在,则删除
if os.path.exists(repo_dir):
    shutil.rmtree(repo_dir)

repo = Repo.clone_from(repo_url, repo_dir)

# 创建epub书籍
book = epub.EpubBook()
book.set_title('My Code Book')
book.add_author('Author Name')  # 替换为实际的作者名字

# 支持的代码文件扩展名
code_extensions = ['.js', '.ts', '.jsx', '.tsx', '.vue', '.py']

# 初始化书籍的章节列表
book_spine = ['nav']

# 生成代码高亮的CSS样式
formatter = HtmlFormatter(style='friendly')
css_content = formatter.get_style_defs('.highlight')
default_css = epub.EpubItem(uid="style_default", media_type="text/css", content=css_content)
book.add_item(default_css)

# 遍历代码文件
for root, dirs, files in os.walk(repo.working_dir):
    for file in files:
        if any(file.endswith(ext) for ext in code_extensions):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                lexer = get_lexer_for_filename(file_path)
                highlighted_code = highlight(content, lexer, formatter)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

            # 创建章节
            title = file  # 使用文件名作为章节标题
            c = epub.EpubHtml(title=title, file_name=f'chap_{file}.xhtml', lang='en')
            c.content = f'<h1>{title}</h1>{highlighted_code}'
            book.add_item(c)
            book_spine.append(c)

# 设置书籍目录
book.toc = tuple(book_spine[1:])  # 第一个元素是'nav'，所以从第二个元素开始
book.spine = book_spine

# 添加封面
book.set_cover("cover.jpg", open("cover.avif", "rb").read())

# 生成epub文件
epub.write_epub('codebook.epub', book)