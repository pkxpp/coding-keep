---
name: coding-keep
description: >
  Preserve file encoding and line ending format when editing files. Automatically detects the original
  encoding (GBK, UTF-8, UTF-8-BOM, UTF-16, etc.) and line ending (LF or CRLF), and ensures edits are
  saved with the same encoding and line ending. Use this skill whenever you need to modify a file that
  might not be UTF-8 or might use CRLF line endings — especially .cpp, .h, .cs, .java, .xml, .ini,
  .cfg, .bat, .rc, .properties, or any file on a Chinese-language Windows system. Also use when the
  user mentions encoding, GBK, UTF-8-BOM, 乱码, 编码, line ending, CRLF, LF, 换行, or when editing
  files in legacy codebases, game engines, or Windows-native projects. Even if the user doesn't mention
  encoding or line endings explicitly, if you're editing a non-UTF-8 file or a file with CRLF endings,
  this skill prevents corruption.
---

# Coding Keep: Encoding & Line Ending Preserving File Editor

## Why this matters

On Windows (especially Chinese-language environments), files are often saved in GBK, UTF-8-BOM,
or other non-standard encodings. Claude's built-in Edit and Write tools always use UTF-8,
which **corrupts** files in other encodings. Once a GBK file is rewritten as UTF-8, all
Chinese characters become garbled, and the file may break builds, crash parsers, or cause
runtime errors.

Additionally, files on Windows typically use CRLF (`\r\n`) line endings, while Unix/Linux files
use LF (`\n`). Claude's Edit and Write tools may not preserve the original line ending format,
causing unintended conversions (e.g., LF → CRLF or vice versa), which creates noisy diffs and
can break tools that are sensitive to line endings.

This skill ensures that **neither encoding nor line ending format ever changes** when editing.

## When to activate

Before using the **Edit** or **Write** tool on any file, run the detection script first.
If the file is UTF-8 (without BOM) with LF line endings, it's safe to use Edit/Write normally.
If it's anything else (non-UTF-8 encoding, BOM, or CRLF line endings), use the preserving edit
script instead.

## Workflow

### Step 1: Detect encoding and line ending before editing

For every file you're about to modify, detect its encoding and line ending format:

```bash
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py <filepath>
```

Example output:
```
[coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf
```

When you see the results, **tell the user**, e.g.:
> `src/main.cpp` 的编码是 **gbk**，换行格式是 **crlf**，将使用编码和换行保持方式编辑。

Possible encodings: `utf-8`, `utf-8-bom`, `gbk`, `utf-16`, `utf-16-le`, `utf-16-be`
Possible line endings: `lf`, `crlf`

### Step 2: Choose the right editing method

| Encoding | Line Ending | Safe to use Edit/Write? | Action |
|---|---|---|---|
| utf-8 | lf | Yes | Use Claude's Edit tool normally |
| utf-8 | crlf | No* | CRLF may be converted to LF; use `encoding_edit.py` |
| utf-8-bom | any | No | BOM will be stripped; use `encoding_edit.py` |
| gbk | any | No | Characters will be corrupted; use `encoding_edit.py` |
| utf-16* | any | No | File will be corrupted; use `encoding_edit.py` |
| any other | any | No | Use `encoding_edit.py` |

\* On Windows, Edit/Write in text mode may translate CRLF → LF, so always use `encoding_edit.py` when CRLF preservation matters.

### Step 3: Edit with encoding and line ending preservation

If the file is NOT plain UTF-8 with LF line endings, use the preserving edit script. The script
will print the detected encoding and line ending before editing, and confirm both are preserved
after saving:

```
[coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf
[coding-keep] src/main.cpp — saved, encoding preserved: gbk, line ending preserved: crlf
```

After the edit, **tell the user**, e.g.:
> `src/main.cpp` 已保存，编码保持不变：**gbk**，换行格式保持不变：**crlf**

**Replace text** (like Edit tool, but encoding & line-ending-safe):
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --replace "old text" "new text"
```

**Replace text from files** (avoids shell escaping / security-check issues with `#include` etc.):
```bash
# Write old/new text to temporary files, then:
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --replace-file /tmp/old.txt /tmp/new.txt
```

Multiple replacements in one pass:
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --replace "old1" "new1" \
  --replace "old2" "new2"
```

**Append text** to end of file:
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --append "text to add"
```

**Append text from file**:
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --append-file /tmp/append.txt
```

**Prepend text** to beginning of file:
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --prepend "text to add"
```

**Prepend text from file**:
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --prepend-file /tmp/prepend.txt
```

**Insert text at a specific line** (1-based):
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --insert-at 42 "new line content"
```

**Insert text from file at a specific line** (1-based):
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --insert-at-file 42 /tmp/insert.txt
```

**Override encoding** (if detection is wrong):
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --encoding gbk --replace "old" "new"
```

**Override line ending** (if detection is wrong):
```bash
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py <filepath> \
  --line-ending crlf --replace "old" "new"
```

### Step 4: Verify

After editing, re-detect to confirm neither encoding nor line ending has changed:

```bash
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py <filepath>
```

Example output:
```
[coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf
```

Both the encoding and line ending should match what they were before the edit. If they match, confirm to the user:
> 验证通过，`src/main.cpp` 仍为 **gbk** 编码，**crlf** 换行。

## Important notes

- **New files** default to UTF-8 (no BOM) with LF line endings. Only use this skill for *existing* files.
- **Binary files** (images, compiled files) should never be edited as text.
- If `chardet` gives low confidence, check the file manually or ask the user what encoding it should be.
- The `--replace` flag replaces only the **first** occurrence. If you need to replace all occurrences, use multiple `--replace` flags or handle it in a script.
- When reading a non-UTF-8 file to understand its content, use the Read tool — it handles most encodings. The encoding/line-ending concern is specifically for **writing back**.
- The script reads and writes in binary mode to avoid any Python text-mode newline translation, guaranteeing line ending preservation.

## Quick reference for common scenarios

**Editing a GBK .cpp file with CRLF:**
```bash
# Detect
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py src/main.cpp
# → [coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf

# Edit
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py src/main.cpp \
  --replace "旧代码" "新代码"
# → [coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf
# → [coding-keep] src/main.cpp — saved, encoding preserved: gbk, line ending preserved: crlf

# Verify
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py src/main.cpp
# → [coding-keep] src/main.cpp — detected encoding: gbk, line ending: crlf
```

**Adding a line to a UTF-8-BOM .xml file with CRLF:**
```bash
# Detect
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py config.xml
# → [coding-keep] config.xml — detected encoding: utf-8-bom, line ending: crlf

# Append
python ~/.claude/skills/coding-keep/scripts/encoding_edit.py config.xml \
  --append '<item key="new" value="added"/>'
# → [coding-keep] config.xml — detected encoding: utf-8-bom, line ending: crlf
# → [coding-keep] config.xml — saved, encoding preserved: utf-8-bom, line ending preserved: crlf

# Verify
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py config.xml
# → [coding-keep] config.xml — detected encoding: utf-8-bom, line ending: crlf
```

**Editing a UTF-8 .h file with LF (safe to use Edit tool):**
```bash
# Detect
python ~/.claude/skills/coding-keep/scripts/detect_encoding.py include/types.h
# → [coding-keep] include/types.h — detected encoding: utf-8, line ending: lf

# Safe to use Claude's Edit tool directly — no encoding or line ending issues
```
