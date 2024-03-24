# Code2Epub Converter

## 简介

Code2Epub Converter 是一个用于将代码仓库转换成 EPUB 格式电子书的工具。它可以遍历指定的代码仓库，将代码文件转换为 EPUB 格式的章节，方便在支持 EPUB 格式的电子书阅读器上阅读和查看代码。

## 安装

本项目依赖于 Python 3 和一些第三方库。在开始之前，请确保您的系统已经安装了 Python 3（推荐 Python 3.6 或更高版本）。

### 安装 Python 3

请访问 [Python 官网](https://www.python.org/) 下载并安装适合您操作系统的 Python 3 版本。

### 安装依赖

本项目依赖于以下库：

- `ebooklib`: 用于生成 EPUB 文件。
- `pygments`: 用于代码高亮。
- `python-dotenv`: 用于从 `.env` 文件加载环境变量。

您可以通过以下命令安装这些依赖：

```bash
pip install ebooklib pygments python-dotenv
```

## 配置

1. 在项目根目录下创建一个 `.env` 文件，并配置您的代码仓库路径。例如：

```env
REPO_URL=https://your-repository-url-here.git
```

请将 `https://your-repository-url-here.git` 替换为您的代码仓库的实际 URL。

## 使用方法

1. 确保您已经在 `.env` 文件中正确配置了仓库 URL。
2. 运行 Code2Epub Converter。脚本会读取 `.env` 文件中的 `REPO_URL`，克隆仓库并开始转换过程。

```bash
python code2epub.py
```

## 功能特点

- **代码高亮**：利用 `pygments` 实现代码高亮，使代码更易读。
- **自动目录生成**：根据代码仓库的结构自动生成 EPUB 的目录，方便快速导航。
- **文件名冲突处理**：通过将文件路径转换为唯一文件名来避免文件名冲突。
- **环境变量支持**：支持从 `.env` 文件加载配置，简化配置过程。

## 贡献

欢迎通过 GitHub Pull Requests 或 Issues 提交贡献或反馈。

## 许可证

本项目采用 MIT 许可证。有关详细信息，请查看 `LICENSE` 文件。