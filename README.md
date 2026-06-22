# coding-keep

一个 kscc skill，用于在编辑文件时自动保持原始文件的编码格式和换行符。

## 功能

- 自动检测文件的原始编码（GBK、UTF-8、UTF-8-BOM、UTF-16 等）
- 自动检测换行符格式（LF 或 CRLF）
- 编辑后以相同的编码和换行符保存，防止文件损坏或乱码

## 适用场景

- 旧代码库中的 GBK 编码文件
- Windows 项目的 CRLF 换行文件
- 游戏引擎、Windows 原生项目中的 `.cpp`、`.h`、`.cs`、`.java`、`.xml`、`.ini`、`.cfg`、`.bat`、`.rc`、`.properties` 等文件
- 任何非 UTF-8 编码或使用 CRLF 换行的文件

## 触发关键词

`encoding`、`GBK`、`UTF-8-BOM`、`乱码`、`编码`、`line ending`、`CRLF`、`LF`、`换行`
