from ebooklib import epub

book = epub.EpubBook()

# 添加书籍的元数据
# book.set_identifier('id123456')
book.set_title('Sample Book')
book.set_language('en')

book.add_author('Author Name')

# 创建CSS样式
css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content=open("style/default.css", "r").read())
book.add_item(css)

# 创建一个章节
c1 = epub.EpubHtml(title='Introduction', file_name='chap_01.xhtml', lang='en')
c1.content = '<h1>Introduction</h1><p>This is the introduction.</p>'
c1.add_item(css)

# 将章节添加到书籍中
book.add_item(c1)

# 定义书籍目录
book.toc = (epub.Link('chap_01.xhtml', 'Introduction', 'intro'),)

# 添加默认的NCX和封面
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# 定义书籍的阅读顺序
book.spine = ['nav', c1]

# 生成EPUB文件
epub.write_epub('test.epub', book, {})