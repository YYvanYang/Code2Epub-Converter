import os
import subprocess
from ebooklib import epub
import html

# 克隆GitHub仓库的函数
def clone_github_repo(repo_url, local_dir):
    if os.path.exists(local_dir):
        # 如果目录已存在，先删除
        subprocess.run(['rm', '-rf', local_dir], check=True)
    # 克隆仓库
    subprocess.run(['git', 'clone', repo_url, local_dir], check=True)

# 从文件扩展名获取media_type
def get_media_type(filename):
    if filename.endswith('.js') or filename.endswith('.jsx'):
        return 'application/javascript'
    elif filename.endswith('.ts') or filename.endswith('.tsx'):
        return 'application/typescript'
    elif filename.endswith('.py'):
        return 'text/x-python'
    else:
        return 'text/plain'

# 克隆仓库
repo_url = 'https://github.com/YYvanYang/ai-gateway-openai-wrapper.git'
local_dir = 'repo'
clone_github_repo(repo_url, local_dir)

book = epub.EpubBook()

# 书籍元数据
book.set_identifier('id123456')
book.set_title('ai-gateway-openai-wrapper')  # 仓库名作为书名
book.set_language('en')

book.add_author('YYvanYang')  # 仓库作者作为书籍作者

# 创建CSS样式
css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content="body { font-family: Times, serif; margin: 20px; }")
book.add_item(css)

# 遍历repo目录，为支持的文件创建章节
for root, dirs, files in os.walk(local_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.py', '.jsx', '.tsx')):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 转义HTML特殊字符
                content_escaped = html.escape(content)
                # 创建章节
                chapter = epub.EpubHtml(title=file, file_name=file + '.xhtml', lang='en')
                chapter.content = f'<h1>{file}</h1><pre><code>{content_escaped}</code></pre>'
                chapter.add_item(css)
                book.add_item(chapter)
                book.spine.append(chapter)

# 添加默认的NCX和封面
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# 生成EPUB文件
epub.write_epub('test.epub', book, {})
