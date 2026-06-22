#!/usr/bin/env python3
"""
Encoding and line-ending preserving file editor.

Reads a file with its detected encoding and line ending format,
applies text replacements, and writes it back preserving both.

Usage:
  python encoding_edit.py <filepath> --replace "old_text" "new_text" [--replace ...]
  python encoding_edit.py <filepath> --append "text to append"
  python encoding_edit.py <filepath> --prepend "text to prepend"
  python encoding_edit.py <filepath> --insert-at <line_number> "text to insert"
"""

import sys
import argparse
from pathlib import Path

# Import detect functions from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from detect_encoding import detect_encoding, detect_line_ending


ENCODING_MAP = {
    "utf-8-bom": "utf-8-sig",  # Python's name for UTF-8 BOM
}

LINE_ENDING_MAP = {
    "crlf": "\r\n",
    "lf": "\n",
}


def get_python_encoding(detected_enc: str) -> str:
    """Convert our encoding name to Python's open() encoding name."""
    return ENCODING_MAP.get(detected_enc, detected_enc)


def read_file_raw(filepath: str):
    """Read file as raw bytes, detect encoding and line ending, decode to string.

    Returns (content_str, detected_encoding, detected_line_ending).
    The content_str uses \\n line endings (Python-normalized).
    """
    raw = Path(filepath).read_bytes()
    if not raw:
        return "", "utf-8", "lf"

    encoding = detect_encoding(filepath)
    line_ending = detect_line_ending(filepath)
    py_enc = get_python_encoding(encoding)

    content = raw.decode(py_enc)
    # Normalize all line endings to \n for manipulation
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    return content, encoding, line_ending


def write_file_preserving(filepath: str, content: str, encoding: str, line_ending: str):
    """Write content to file preserving original encoding and line ending format.

    content uses \\n internally; we convert to the target line ending before writing.
    """
    py_enc = get_python_encoding(encoding)
    le_str = LINE_ENDING_MAP.get(line_ending, "\n")

    # Convert internal \n to target line ending
    output = content.replace("\n", le_str)

    # Encode and write as bytes to avoid any Python text-mode newline translation
    Path(filepath).write_bytes(output.encode(py_enc))


def apply_replacements(content: str, replacements: list):
    """Apply a list of (old, new) replacements to content."""
    for old, new in replacements:
        if old not in content:
            print(f"WARNING: replacement text not found: {old[:80]}...", file=sys.stderr)
            continue
        content = content.replace(old, new, 1)
    return content


def main():
    parser = argparse.ArgumentParser(description="Encoding and line-ending preserving file editor")
    parser.add_argument("filepath", help="File to edit")
    parser.add_argument("--replace", nargs=2, action="append", metavar=("OLD", "NEW"),
                        help="Replace OLD with NEW (can be repeated)")
    parser.add_argument("--replace-file", nargs=2, action="append", metavar=("OLD_FILE", "NEW_FILE"),
                        help="Replace using text from files (avoids shell escaping issues)")
    parser.add_argument("--append", metavar="TEXT", help="Append text to end of file")
    parser.add_argument("--append-file", metavar="FILE", help="Append text from file to end of file")
    parser.add_argument("--prepend", metavar="TEXT", help="Prepend text to beginning of file")
    parser.add_argument("--prepend-file", metavar="FILE", help="Prepend text from file to beginning of file")
    parser.add_argument("--insert-at", nargs=2, metavar=("LINE", "TEXT"),
                        help="Insert text at line number (1-based)")
    parser.add_argument("--insert-at-file", nargs=2, metavar=("LINE", "FILE"),
                        help="Insert text from file at line number (1-based)")
    parser.add_argument("--encoding", default=None,
                        help="Override encoding detection (e.g., gbk, utf-8, utf-8-bom)")
    parser.add_argument("--line-ending", default=None, choices=["lf", "crlf"],
                        help="Override line ending detection (lf or crlf)")

    args = parser.parse_args()

    filepath = args.filepath
    content, encoding, line_ending = read_file_raw(filepath)

    # Allow overrides
    if args.encoding:
        encoding = args.encoding
    if args.line_ending:
        line_ending = args.line_ending

    # Always show detected encoding and line ending upfront
    print(f"[coding-keep] {filepath} — detected encoding: {encoding}, line ending: {line_ending}")

    changed = False

    if args.replace:
        content = apply_replacements(content, args.replace)
        changed = True

    if args.replace_file:
        file_replacements = []
        for old_file, new_file in args.replace_file:
            old_text = Path(old_file).read_text(encoding="utf-8")
            new_text = Path(new_file).read_text(encoding="utf-8")
            # Strip trailing newline added by editor if present
            if old_text.endswith("\n"):
                old_text = old_text[:-1]
            if new_text.endswith("\n"):
                new_text = new_text[:-1]
            file_replacements.append((old_text, new_text))
        content = apply_replacements(content, file_replacements)
        changed = True

    if args.append:
        # Ensure newline before append if file doesn't end with one
        if content and not content.endswith("\n"):
            content += "\n"
        content += args.append
        changed = True

    if args.append_file:
        text = Path(args.append_file).read_text(encoding="utf-8")
        if text.endswith("\n"):
            text = text[:-1]
        if content and not content.endswith("\n"):
            content += "\n"
        content += text
        changed = True

    if args.prepend:
        content = args.prepend + content
        changed = True

    if args.prepend_file:
        text = Path(args.prepend_file).read_text(encoding="utf-8")
        if text.endswith("\n"):
            text = text[:-1]
        content = text + content
        changed = True

    if args.insert_at:
        line_num = int(args.insert_at[0])
        text = args.insert_at[1]
        lines = content.split("\n")
        idx = max(0, min(line_num - 1, len(lines)))
        lines.insert(idx, text)
        content = "\n".join(lines)
        changed = True

    if args.insert_at_file:
        line_num = int(args.insert_at_file[0])
        text = Path(args.insert_at_file[1]).read_text(encoding="utf-8")
        if text.endswith("\n"):
            text = text[:-1]
        lines = content.split("\n")
        idx = max(0, min(line_num - 1, len(lines)))
        lines.insert(idx, text)
        content = "\n".join(lines)
        changed = True

    if changed:
        write_file_preserving(filepath, content, encoding, line_ending)
        print(f"[coding-keep] {filepath} — saved, encoding preserved: {encoding}, line ending preserved: {line_ending}")
    else:
        print(f"[coding-keep] {filepath} — no edits applied")


if __name__ == "__main__":
    main()
