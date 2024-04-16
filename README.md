# Code to Ebook Converter

This project allows you to convert a GitHub repository containing code files into an EPUB and PDF ebook.

## Features

- Downloads a GitHub repository and extracts the code files
- Applies syntax highlighting to the code using Pygments library
- Generates an EPUB ebook with a table of contents
- Generates a PDF ebook with a table of contents and page numbers

## Requirements

- Python 3.7+
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/code-to-ebook.git
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Configure the `config.ini` file with your desired settings:

   - Set the `repo_url` to the GitHub repository you want to convert
   - Adjust other settings as needed

2. Run the script:

   ```
   python code2epub.py
   ```

   You can also provide command-line arguments to override the configuration:

   ```
   python code2epub.py --repo-url https://github.com/user/repo --output-dir ./ebooks --log-level DEBUG
   ```

3. The generated EPUB and PDF files will be saved in the specified output directory.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
