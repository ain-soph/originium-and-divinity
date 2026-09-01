#!/usr/bin/env python3
"""将《源石与神灵》的正文、章节草稿与可见思路资料汇编成单个 Markdown。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "源石与神灵-完整汇编.md"
VOLUMES = ["第一卷 巨熊喋血", "第二卷 十字军之神", "第三卷 那座塔"]
SUPPLEMENTS = [ROOT / "草稿.md", ROOT / "第三卷 那座塔" / "README.md"]


def natural_key(path: Path) -> tuple:
    """依文件名中的卷-章数字排序，支持 1-4.5。"""
    match = re.search(r"(\d+)-(\d+(?:\.\d+)?)", path.name)
    if match:
        return (int(match.group(1)), float(match.group(2)), path.name)
    return (999, 999.0, path.name)


def title_for(path: Path) -> str:
    title = path.stem
    title = re.sub(r"^（草稿）", "", title)
    return title.strip()


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
        "# 源石与神灵·完整汇编",
        "",
        "> 本文件由 `build_complete_markdown.py` 自动生成。原始文件保持不变；请不要直接编辑本汇编，否则下次生成时会被覆盖。",
        "> “草稿”状态、空章节与重复章节均依原目录如实保留。",
        "",
        "## 目录",
        "",
        "- [小说简介](#小说简介)",
        "- [第一卷 巨熊喋血](#第一卷-巨熊喋血)",
        "- [第二卷 十字军之神](#第二卷-十字军之神)",
        "- [第三卷 那座塔](#第三卷-那座塔)",
        "- [创作思路与补充资料](#创作思路与补充资料)",
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
        chapter_files = [path for path in chapter_files if path.name != "README.md"]
        for path in chapter_files:
            state = " （草稿）" if path.name.startswith("（草稿）") else ""
            append_source(lines, path, f"### {title_for(path)}{state}", seen)

    lines.extend(["## 创作思路与补充资料", ""])
    for path in SUPPLEMENTS:
        if path.exists():
            append_source(lines, path, f"### {title_for(path)}", seen)

    for path in sorted((ROOT / "fable").glob("*.md"), key=natural_key):
        append_source(lines, path, f"### Fable 记录 {path.stem}", seen)

    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"已生成：{OUTPUT}")
