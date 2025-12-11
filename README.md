# [Pixiv Encyclopedia Viewer History Extractor](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor "Pixiv Encyclopedia Viewer History Extractor")

[![CodeQL Advanced](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/codeql.yml/badge.svg)](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/codeql.yml)

An Extraction Tool for Pixiv Encyclopedia Viewer Count History

## Japanese README
日本語版はこちら [`README.ja.md`](README.ja.md).

---

## Overview

Extract daily view history data from a [Pixiv Encyclopedia (pixiv百科事典)](https://dic.pixiv.net/) article.

The script reads the JSON payload embedded in the page (`__NEXT_DATA__`), extracts the `/get_graph_data` → `tagCounts` section, and outputs a simple time series of `{date, count}`.

> ⚠️ **Unofficial tool**  
> This project is not affiliated with or endorsed by Pixiv.  
> Please follow Pixiv's Terms of Use and robots.txt when using this script.


## Features

- Fetch by **article title** (e.g., `"ブルーアーカイブ"`) directly from Pixiv Encyclopedia
- Or read from a **local HTML file**
- Output **JSON Lines** to stdout  
  (one `{"date": "...","count": ...}` per line)
- Optional **CSV export** via `--csv output.csv`

---


## Requisites

- Python 3.8+
- Dependencies:
  - `requests`
  - `beautifulsoup4`

---

## Usage

### 0. Create virtual environment

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 1. Fetch by article title

```bash
python src/extract_viewer_history.py "ブルーアーカイブ"
```

This will:

- Download `https://dic.pixiv.net/a/ブルーアーカイブ`
- Parse the embedded JSON
- Print one JSON object per line to stdout:

```json
{"date": "2025-07-01", "count": 141}
{"date": "2025-07-02", "count": 132}
{"date": "2025-07-03", "count": 213}
...
```

You can redirect it to a file:

```bash
python src/extract_viewer_history.py "ブルーアーカイブ" > ブルーアーカイブ.jsonl
```

### 2. Export as CSV

Use the `--csv` option to write a CSV file while still printing JSON to stdout:

```bash
python src/extract_viewer_history.py "ブルーアーカイブ" --csv ブルーアーカイブ.csv
```

Example CSV content:

```csv
date,count
2025-07-01,141
2025-07-02,132
2025-07-03,213
...
```

### 3. Use a local HTML file

If you have already saved the article HTML:

```bash
python src/extract_viewer_history.py ブルーアーカイブ.html
python src/extract_viewer_history.py ブルーアーカイブ.html --csv ブルーアーカイブ.csv
```

The script will detect that `ブルーアーカイブ.html` is a file and will parse it instead of fetching from the web.

---

###　4. Test

```bash
pip install -r requirements.test.txt
pytest'
```

### 5. Deactivate environment

```bash
deactivate
```


---

## Notes / Limitations

- The script relies on the current internal JSON structure of Pixiv Encyclopedia pages (Next.js `__NEXT_DATA__`).  
  If Pixiv changes their frontend implementation, this script may break.
- No rate limiting is implemented; please:
  - Use it responsibly
  - Avoid sending many requests in a short time
- This is a simple utility script, primarily intended for personal analysis or research.

---

## License
- Apache License 2.0