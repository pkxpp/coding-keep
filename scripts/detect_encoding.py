#!/usr/bin/env python3
"""Detect the encoding and line ending format of one or more files."""

import sys
import chardet
from pathlib import Path


def _try_decode(raw: bytes, encoding: str) -> bool:
    """Check if raw bytes can be decoded with the given encoding without errors."""
    try:
        raw.decode(encoding)
        return True
    except (UnicodeDecodeError, LookupError):
        return False


def detect_encoding(filepath: str) -> str:
    """Detect file encoding using chardet, with CJK-aware refinement."""
    raw = Path(filepath).read_bytes()
    if not raw:
        return "utf-8"

    # BOM detection takes absolute priority
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-bom"
    elif raw[:2] == b"\xff\xfe":
        return "utf-16-le"
    elif raw[:2] == b"\xfe\xff":
        return "utf-16-be"

    # Pure ASCII → treat as utf-8
    if all(b < 0x80 for b in raw):
        return "utf-8"

    # Try UTF-8 first (most common, fast check)
    if _try_decode(raw, "utf-8"):
        return "utf-8"

    # Try GBK (common on Chinese Windows) before chardet,
    # because chardet often mislabels short GBK files as koi8-r, ISO-8859-*, etc.
    if _try_decode(raw, "gbk"):
        return "gbk"

    # Fall back to chardet
    result = chardet.detect(raw)
    encoding = result["encoding"] or "utf-8"

    # Normalize chardet output names
    mapping = {
        "ASCII": "utf-8",
        "GB2312": "gbk",
        "GB18030": "gbk",
        "UTF-8-SIG": "utf-8-bom",
        "UTF-16": "utf-16",
        "UTF-16LE": "utf-16-le",
        "UTF-16BE": "utf-16-be",
        # Common chardet misidentifications of GBK
        "ISO-8859-1": "gbk",
        "ISO-8859-2": "gbk",
        "KOI8-R": "gbk",
        "WINDOWS-1252": "gbk",
        "WINDOWS-1251": "gbk",
    }
    encoding = mapping.get(encoding.upper(), encoding.lower())

    # Verify: if we mapped to gbk, make sure it actually decodes
    if encoding == "gbk" and not _try_decode(raw, "gbk"):
        encoding = result["encoding"].lower() if result["encoding"] else "utf-8"

    return encoding


def detect_line_ending(filepath: str) -> str:
    """Detect the dominant line ending format: 'lf' or 'crlf'."""
    raw = Path(filepath).read_bytes()
    if not raw:
        return "lf"

    crlf_count = raw.count(b"\r\n")
    # Count bare LF (not preceded by CR) — scan byte by byte
    bare_lf_count = 0
    i = 0
    while i < len(raw):
        if raw[i:i+1] == b"\n":
            if i == 0 or raw[i-1:i] != b"\r":
                bare_lf_count += 1
            i += 1
        else:
            i += 1

    if crlf_count == 0 and bare_lf_count == 0:
        return "lf"  # no line breaks at all, default to lf

    if crlf_count >= bare_lf_count:
        return "crlf"
    else:
        return "lf"


def main():
    if len(sys.argv) < 2:
        print("Usage: detect_encoding.py <file1> [file2] ...", file=sys.stderr)
        sys.exit(1)

    for filepath in sys.argv[1:]:
        p = Path(filepath)
        if not p.exists():
            print(f"[coding-keep] {filepath} — file not found", file=sys.stderr)
            continue
        enc = detect_encoding(filepath)
        le = detect_line_ending(filepath)
        print(f"[coding-keep] {filepath} — detected encoding: {enc}, line ending: {le}")


if __name__ == "__main__":
    main()
