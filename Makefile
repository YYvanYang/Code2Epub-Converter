.PHONY: all install clean run help check-deps default

# 设置默认目标为 all
.DEFAULT_GOAL := all

PYTHON := python3
PIP := pip3
VENV := venv
VENV_BIN := $(VENV)/bin

help:
	@echo "使用说明:"
	@echo "make          - 执行完整流程(安装依赖并运行)"
	@echo "make install  - 创建虚拟环境并安装依赖"
	@echo "make run     - 运行程序生成电子书"
	@echo "make clean   - 清理生成的文件和虚拟环境"

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip

check-deps:
	@echo "检查系统依赖..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		if ! brew list libmagic > /dev/null 2>&1; then \
			echo "Installing libmagic..."; \
			brew install libmagic; \
		fi; \
		if ! brew list wkhtmltopdf > /dev/null 2>&1; then \
			echo "Installing wkhtmltopdf..."; \
			brew install wkhtmltopdf; \
		fi \
	elif [ "$(shell uname)" = "Linux" ]; then \
		if ! dpkg -l | grep -q "libmagic1"; then \
			sudo apt-get install -y libmagic1; \
		fi; \
		if ! dpkg -l | grep -q "wkhtmltopdf"; then \
			sudo apt-get install -y wkhtmltopdf; \
		fi \
	fi

install: check-deps
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@echo "依赖安装完成"

run:
	@if [ ! -d "$(VENV)" ]; then \
		echo "请先运行 'make install' 安装依赖"; \
		exit 1; \
	fi
	$(VENV_BIN)/python code2epub.py

clean:
	rm -rf $(VENV)
	rm -rf repo/
	rm -rf output/
	rm -rf __pycache__/
	rm -rf *.log

# 定义默认目标
default: all

# 主要目标
all: install run

# 系统依赖检查
check-system-deps:
	@echo "检查系统依赖..."
	@which python3 >/dev/null 2>&1 || (echo "请先安装 Python 3" && exit 1)
	@which git >/dev/null 2>&1 || (echo "请先安装 Git" && exit 1)
	@if [ "$(shell uname)" = "Linux" ]; then \
		(dpkg -l | grep -q "libcairo2-dev") || echo "请安装 libcairo2-dev"; \
		(dpkg -l | grep -q "libpango1.0-dev") || echo "请安装 libpango1.0-dev"; \
		(dpkg -l | grep -q "libgdk-pixbuf2.0-dev") || echo "请安装 libgdk-pixbuf2.0-dev"; \
		(dpkg -l | grep -q "libffi-dev") || echo "请安装 libffi-dev"; \
	fi