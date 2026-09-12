#!/usr/bin/env python3
"""汇编《源石与神灵》，排除文件名含“草稿”的资料。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "源石与神灵.md"
VOLUMES = ["第一卷 巨熊喋血", "第二卷 十字军之神", "第三卷 那座塔"]


def natural_key(path: Path) -> tuple:
    """依文件名中的卷-章数字排序，支持 1-4.5。"""
    match = re.search(r"(\d+)-(\d+(?:\.\d+)?)", path.name)
    if match:
        return (int(match.group(1)), float(match.group(2)), path.name)
    return (999, 999.0, path.name)


def title_for(path: Path) -> str:
    return path.stem.strip()


def shifted_headings(text: str, levels: int = 3) -> str:
    """将源文内标题下移，不打乱汇编的卷/章层级。"""
    def replace(match: re.Match[str]) -> str:
        return "#" * min(6, len(match.group(1)) + levels) + match.group(2)

    return re.sub(r"^(#{1,6})(\s+)", replace, text, flags=re.MULTILINE)


def read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    return shifted_headings(text)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def image_markdown_for(chapter: Path) -> list[str]:
    match = re.search(r"(\d+-\d+(?:\.\d+)?)", chapter.name)
    if not match:
        return []
    prefix = match.group(1)
    images = sorted(chapter.parent.glob(f"{prefix} *.png"), key=natural_key)
    if not images:
        return []
    lines = ["", "#### 章节配图", ""]
    for image in images:
        lines.append(f"![{image.stem}]({rel(image)})")
        lines.append("")
    return lines


def append_source(lines: list[str], path: Path, heading: str, seen: dict[str, Path]) -> None:
    if "草稿" in path.name:
        return
    lines.extend([heading, "", f"> 来源：`{rel(path)}`", ""])
    if path.stat().st_size == 0:
        lines.extend(["*（空文件，保留章节占位）*", ""])
        return

    file_digest = digest(path)
    duplicate = seen.get(file_digest)
    if duplicate is not None:
        lines.extend([f"> 注：本文件与 `{rel(duplicate)}` 内容完全相同；仍按原章号完整保留。", ""])
    else:
        seen[file_digest] = path

    lines.extend([read_text(path), ""])
    lines.extend(image_markdown_for(path))


def build() -> str:
    lines = [
        "# 源石与神灵",
        "",
        # "> 本文件由 `build_complete_markdown.py` 自动生成。原始文件保持不变；请不要直接编辑本汇编，否则下次生成时会被覆盖。",
        # "",
        "## 目录",
        "",
        "- [小说简介](#小说简介)",
        "- [第一卷 巨熊喋血](#第一卷-巨熊喋血)",
        "- [第二卷 十字军之神](#第二卷-十字军之神)",
        "- [第三卷 那座塔](#第三卷-那座塔)",
        "- [幕后](#幕后)",
        "",
        "## 小说简介",
        "",
        f"> 来源：`{rel(ROOT / 'README.md')}`",
        "",
        read_text(ROOT / "README.md"),
        "",
    ]

    seen: dict[str, Path] = {}
    for volume in VOLUMES:
        lines.extend([f"## {volume}", ""])
        chapter_files = sorted((ROOT / volume).glob("*.md"), key=natural_key)
        chapter_files = [
            path for path in chapter_files
            if path.name != "README.md"
        ]
        for path in chapter_files:
            append_source(lines, path, f"### {title_for(path)}", seen)

    lines.extend(["## 幕后", ""])
    for path in sorted((ROOT / "幕后").glob("*.md"), key=natural_key):
        if path.name != "README.md":
            append_source(lines, path, f"### {title_for(path)}", seen)

    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"已生成：{OUTPUT}")
