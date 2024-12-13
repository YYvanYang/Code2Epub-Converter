# Code2EPUB

将代码仓库转换为EPUB和PDF格式的文档工具。

## 功能特性

- 支持从GitHub克隆代码仓库
- 自动检测文件编码
- 生成PDF和EPUB格式文档
- 支持代码高亮
- 支持中文显示
- 自定义LaTeX模板

## 安装要求

- Python 3.7+
- pandoc
- XeLaTeX
- Source Han Sans CN字体（中文支持）
- Source Code Pro字体（代码显示）

## 快速开始

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/code2epub.git
   cd code2epub
   ```

2. 安装依赖：
   ```bash
   make setup
   ```

3. 配置：
   编辑 `config.ini` 文件，设置GitHub仓库URL和其他选项。

4. 运行：
   ```bash
   make run
   ```

## 配置说明

在 `config.ini` 文件中：

- `github.repo_url`: GitHub仓库地址
- `output.output_dir`: 输出目录
- `output.supported_extensions`: 支持的文件扩展名

## 目录结构

```
.
├── code2epub.py      # 主程序
├── config.ini        # 配置文件
├── requirements.txt  # Python依赖
├── Makefile         # 构建脚本
└── templates/       # LaTeX模板
    └── latex/
        ├── main.tex
        └── includes/
            └── packages.tex
```

## 许可证

MIT License
