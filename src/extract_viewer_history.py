from __future__ import annotations

"""
Extract daily view history from a Pixiv Encyclopedia (dic.pixiv.net) article.

Usage examples:
    # Fetch by article title (recommended), print JSON Lines
    python extract_viewer_history.py "ブルーアーカイブ"

    # Save view history as CSV as well
    python extract_viewer_history.py "ブルーアーカイブ" --csv ブルーアーカイブ.csv

    # Use a locally saved HTML file instead of fetching
    python extract_viewer_history.py ブルーアーカイブ.html
    python extract_viewer_history.py ブルーアーカイブ.html --csv ブルーアーカイブ.csv

Output (stdout):
    One JSON object per line:
    {"date": "2025-07-01", "count": 141}
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

PIXIV_DIC_BASE_URL = "https://dic.pixiv.net/a/"


def load_html(arg: str) -> str:
    """
    Load HTML source either from a local file or from Pixiv Encyclopedia.

    If `arg` is an existing file path, read that file as HTML.
    Otherwise, treat `arg` as a Pixiv Encyclopedia article title and
    fetch the corresponding page via HTTP.

    Parameters
    ----------
    arg : str
        Article title (e.g. "ブルーアーカイブ") or a local HTML file path.

    Returns
    -------
    str
        HTML source as a string.

    Raises
    ------
    ValueError
        If the title is empty or HTTP request fails.
    """
    path = Path(arg)

    # If a file with this name exists, treat it as a local HTML file.
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")

    # Otherwise, treat `arg` as a Pixiv Encyclopedia article title.
    title = arg.strip()
    if not title:
        raise ValueError("Empty article title is not allowed.")

    # URL-encode the title and build the Pixiv dic URL.
    url = PIXIV_DIC_BASE_URL + quote(title, safe="")

    headers = {
        # A simple desktop User-Agent to avoid being blocked.
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    # Use detected encoding if available; fallback to UTF-8.
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def extract_viewer_history_from_html(html: str) -> List[Dict[str, Any]]:
    """
    Parse Pixiv Encyclopedia HTML and extract the daily view history.

    The view history data is embedded inside a JSON object in a script tag
    with id="__NEXT_DATA__". Under that object, we look for the
    `swrFallback` field and then a key containing "/get_graph_data".
    Inside that graph data, we use the `tagCounts` field.

    Parameters
    ----------
    html : str
        HTML source of a Pixiv Encyclopedia article page.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries with the following keys:
        - "date"  : str, in "YYYY-MM-DD" format
        - "count" : int, view count for that date

    Raises
    ------
    ValueError
        If the expected JSON structure cannot be found or parsed.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find the Next.js data payload.
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        raise ValueError("__NEXT_DATA__ script tag not found in HTML.")

    data = json.loads(script.string)

    try:
        swr = data["props"]["pageProps"]["swrFallback"]
    except KeyError as e:
        raise ValueError("Unexpected JSON structure: 'swrFallback' not found.") from e

    # Find the key that contains "/get_graph_data".
    try:
        key = next(k for k in swr.keys() if "/get_graph_data" in k)
    except StopIteration as e:
        raise ValueError("View history graph data key ('/get_graph_data') not found.") from e

    graph = swr[key]
    if "tagCounts" not in graph:
        raise ValueError("'tagCounts' field is missing in graph data.")

    tag_counts = graph["tagCounts"]

    # `tagCounts` may be a list already, or a JSON-encoded string.
    if isinstance(tag_counts, str):
        data_list = json.loads(tag_counts)
    else:
        data_list = tag_counts

    # Normalize and filter the data.
    result: List[Dict[str, Any]] = [
        {"date": item["date"], "count": item["count"]}
        for item in data_list
        if isinstance(item, dict) and "date" in item and "count" in item
    ]

    if not result:
        raise ValueError("No valid {date, count} entries found in 'tagCounts'.")

    return result


def export_to_csv(series: List[Dict[str, Any]], csv_path: str) -> None:
    """
    Export the view history series to a CSV file.

    Parameters
    ----------
    series : List[Dict[str, Any]]
        List of records, each containing "date" and "count".
    csv_path : str
        Path to the output CSV file. The file will be overwritten if it exists.
    """
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # CSV header
        writer.writerow(["date", "count"])
        for row in series:
            writer.writerow([row.get("date", ""), row.get("count", "")])


def parse_cli_args(argv: List[str]) -> tuple[str, Optional[str]]:
    """
    Parse command-line arguments.

    Parameters
    ----------
    argv : List[str]
        Command-line arguments excluding the script name.

    Returns
    -------
    tuple[str, Optional[str]]
        (title_or_file, csv_path)

        - title_or_file: required argument (Pixiv title or HTML file path)
        - csv_path     : CSV file path if `--csv` option is given, otherwise None

    Raises
    ------
    ValueError
        If required arguments are missing or invalid options are used.
    """
    if not argv:
        raise ValueError("Missing required <title-or-html-file> argument.")

    title_or_file = argv[0]
    csv_path: Optional[str] = None

    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--csv":
            if i + 1 >= len(argv):
                raise ValueError("Missing CSV path after --csv.")
            csv_path = argv[i + 1]
            i += 2
        else:
            # Unknown option; you can change this to raise instead of warning if you prefer strict behavior.
            print(f"warning: unknown argument ignored: {arg}", file=sys.stderr)
            i += 1

    return title_or_file, csv_path


def main(argv: List[str]) -> None:
    """
    Main entry point.

    1. Parse CLI arguments.
    2. Load HTML from a local file or Pixiv Encyclopedia.
    3. Extract daily view history.
    4. Print each record as one JSON line to stdout.
    5. Optionally export the same data to a CSV file.
    """
    title_or_file, csv_path = parse_cli_args(argv)

    html = load_html(title_or_file)
    series = extract_viewer_history_from_html(html)

    # JSON Lines format to stdout
    for row in series:
        print(json.dumps(row, ensure_ascii=False))

    # Optional CSV export
    if csv_path is not None:
        export_to_csv(series, csv_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python extract_viewer_history.py <title-or-html-file> [--csv output.csv]",
            file=sys.stderr,
        )
        print('Example: python extract_viewer_history.py "ブルーアーカイブ" --csv ブルーアーカイブ.csv', file=sys.stderr)
        sys.exit(1)

    try:
        main(sys.argv[1:])
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
