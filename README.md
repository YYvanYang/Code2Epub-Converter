以下是一个简单的 `README.md` 模板，适用于您的项目。这个模板包括了项目简介、安装指南、运行指南和其他可能有用的信息。请根据您的项目特点进行调整。

```markdown
# Code2Epub Converter

## 简介

Code2Epub Converter 是一个用于将代码仓库转换成 EPUB 格式电子书的工具。它可以遍历指定的代码仓库，将代码文件转换为 EPUB 格式的章节，方便在支持 EPUB 格式的电子书阅读器上阅读和查看代码。

## 安装

本项目依赖于 Python 3 和一些第三方库。在开始之前，请确保您的系统已经安装了 Python 3（推荐 Python 3.6 或更高版本）。

### 安装 Python 3

请访问 [Python 官网](https://www.python.org/) 下载并安装适合您操作系统的 Python 3 版本。

### 安装依赖

本项目依赖于 `ebooklib` 库用于生成 EPUB 文件，`pygments` 用于代码高亮。您可以通过以下命令安装这些依赖：

```bash
pip install ebooklib pygments
```

## 使用方法

1. 将您的代码仓库克隆到本地（如果尚未克隆）。例如：

```bash
git clone https://your-repository-url-here
```

2. 运行 Code2Epub Converter，指定代码仓库的本地路径和输出的 EPUB 文件名。例如：

```bash
python code2epub.py /path/to/your/repository output.epub
```

请将 `/path/to/your/repository` 替换为您代码仓库的实际路径，`output.epub` 替换为您希望生成的 EPUB 文件名。

## 功能特点

- **代码高亮**：利用 `pygments` 实现代码高亮，使代码更易读。
- **自动目录生成**：根据代码仓库的结构自动生成 EPUB 的目录，方便快速导航。
- **文件名冲突处理**：通过将文件路径转换为唯一文件名来避免文件名冲突。

## 贡献

欢迎通过 GitHub Pull Requests 或 Issues 提交贡献或反馈。

## 许可证

本项目采用 MIT 许可证。有关详细信息，请查看 `LICENSE` 文件。
```

请注意，上述模板中的 `code2epub.py` 是一个示例脚本文件名，您需要将其替换为您项目的实际入口脚本文件名。此外，根据您的项目特性，可能还需要添加或修改某些部分，例如增加关于如何贡献代码的详细说明、如何报告问题、项目的详细功能介绍等。