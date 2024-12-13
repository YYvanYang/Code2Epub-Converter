# Code to Ebook Converter

一个将GitHub代码仓库转换为EPUB和PDF电子书的工具。支持代码语法高亮、目录生成等功能。

[English](README_EN.md) | 简体中文

## 功能特点

- 自动下载并解析GitHub仓库代码
- 使用Pygments实现代码语法高亮
- 生成包含目录的EPUB电子书
- 生成包含目录和页码的PDF电子书
- 支持多种编程语言
- 支持大文件处理和断点续传
- 可配置的输出格式

## 系统要求

- Python 3.7+
- Git

### macOS 依赖安装
```bash
brew install libmagic wkhtmltopdf
```

### Linux (Ubuntu/Debian) 依赖安装
```bash
sudo apt-get update
sudo apt-get install -y libmagic1 wkhtmltopdf
```

### Windows 依赖安装
1. 下载并安装 [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
2. 将 wkhtmltopdf 添加到系统 PATH

## 快速开始

1. 克隆仓库:
```bash
git clone https://github.com/yourusername/code-to-ebook.git
cd code-to-ebook
```

2. 使用Make命令安装(推荐):
```bash
make install  # 安装依赖
make run      # 运行程序
# 或者一键执行
make all
```

3. 手动安装:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows使用: .\venv\Scripts\activate
pip install -r requirements.txt
python code2epub.py
```

## 配置说明

编辑 `config.ini` 文件来自定义设置:

```ini
[github]
repo_url = https://github.com/user/repo.git
# github_token = your_token  # 可选，用于私有仓库

[output]
output_dir = output
file_name_format = {repo_name}_{timestamp}
supported_extensions = .js,.ts,.py,.jsx,.tsx,.rs,.md
max_file_size_mb = 10

[processing]
max_workers = 4
timeout_seconds = 300

[logging]
level = INFO
log_file = code2epub.log
```

## 命令行参数

```bash
python code2epub.py --help
```

支持的参数:
- `--repo-url`: 指定GitHub仓库URL
- `--output-dir`: 指定输出目录
- `--log-level`: 设置日志级别(DEBUG/INFO/WARNING/ERROR)

## 常见问题

1. **Q: 如何处理私有仓库?**  
   A: 在config.ini中添加GitHub token

2. **Q: 支持哪些编程语言?**  
   A: 支持所有主流编程语言，包括但不限于Python、JavaScript、TypeScript、Rust等

3. **Q: 文件太大怎么办?**  
   A: 可以在配置文件中调整max_file_size_mb参数

## 项目结构

```
.
├── code2epub.py      # 主程序
├── config.ini        # 配置文件
├── requirements.txt  # 依赖列表
├── Makefile         # 构建脚本
└── README.md        # 说明文档
```

## 开发计划

- [ ] 添加更多输出格式支持
- [ ] 优化PDF排版效果
- [ ] 添加批量处理功能
- [ ] 支持自定义样式模板

## 贡献指南

1. Fork 项目
2. 创建新分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- [WeasyPrint](https://weasyprint.org/)
- [EbookLib](https://github.com/aerkalov/ebooklib)
- [Pygments](https://pygments.org/)

## 联系方式

如有问题或建议，欢迎提交 [Issue](https://github.com/yourusername/code-to-ebook/issues)
