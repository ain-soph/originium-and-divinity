#!/usr/bin/env python3
"""汇编《源石与神灵》幕后章节，排除文件名含“草稿”的资料。"""

from __future__ import annotations

import re
from pathlib import Path

from build_complete_markdown import digest, shifted_headings


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "幕后"
OUTPUT = ROOT / "源石与神灵-幕后.md"


def natural_key(path: Path) -> tuple:
    """按章号排序，支持 1.、2.、10. 以及 1.5 等编号。"""
    match = re.match(r"(\d+(?:\.\d+)?)", path.name)
    if match:
        return (0, float(match.group(1)), path.name)
    return (1, 0.0, path.name)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build() -> str:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"幕后章节目录不存在：{SOURCE}")

    chapters = sorted(
        (
            path for path in SOURCE.glob("*.md")
            if path.is_file() and path.name != "README.md" and "草稿" not in path.name
        ),
        key=natural_key,
    )
    lines = [
        "# 源石与神灵·幕后",
        "",
        "> 本文件由 `build_behind_scenes_markdown.py` 自动生成。原始文件保持不变；请不要直接编辑本汇编，否则下次生成时会被覆盖。",
        "",
        "## 目录",
        "",
    ]
    for index, path in enumerate(chapters, start=1):
        lines.append(f"- [{path.stem.strip()}](#chapter-{index})")
    lines.append("")

    seen: dict[str, Path] = {}
    for index, path in enumerate(chapters, start=1):
        lines.extend([
            f'<a id="chapter-{index}"></a>',
            "",
            f"## {path.stem.strip()}",
            "",
            f"> 来源：`{rel(path)}`",
            "",
        ])
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        if not text:
            lines.extend(["*（空文件，保留章节占位）*", ""])
            continue

        file_digest = digest(path)
        duplicate = seen.get(file_digest)
        if duplicate is not None:
            lines.extend([f"> 注：本文件与 `{rel(duplicate)}` 内容完全相同；仍按原章号完整保留。", ""])
        else:
            seen[file_digest] = path

        lines.extend([shifted_headings(text, levels=2), ""])

    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"已生成：{OUTPUT}")
