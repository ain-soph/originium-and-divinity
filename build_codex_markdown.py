#!/usr/bin/env python3
"""将项目 .codex 中的 skill、方法文档与写作记忆汇编为单个 Markdown。"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CODEX = ROOT / ".codex"
OUTPUT = ROOT / "源石与神灵-Codex写作记忆汇编.md"
SKILL = CODEX / "skills" / "write-yuanshi-novel"
MEMORY = CODEX / "memory" / "源石与神灵"
VOLUMES = ["第一卷 巨熊喋血", "第二卷 十字军之神", "第三卷 那座塔"]
REFERENCE_ORDER = [
    "style.md",
    "memory.md",
    "thought-expression.md",
    "character-craft.md",
    "concept-development.md",
    "plot-design.md",
    "character-note-template.md",
    "note-template.md",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def natural_key(path: Path) -> tuple:
    match = re.search(r"(\d+)-(\d+(?:\.\d+)?)", path.name)
    if match:
        return (int(match.group(1)), float(match.group(2)), path.name)
    return (999, 999.0, path.name)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()


def shift_headings(text: str, levels: int) -> str:
    def replace(match: re.Match[str]) -> str:
        return "#" * min(6, len(match.group(1)) + levels) + match.group(2)

    return re.sub(r"^(#{1,6})(\s+)", replace, text, flags=re.MULTILINE)


def append_markdown(lines: list[str], path: Path, heading: str, level: int = 3) -> None:
    lines.extend([f"{'#' * level} {heading}", "", f"> 来源：`{rel(path)}`", ""])
    text = read(path)
    lines.extend([shift_headings(text, level) if text else "*（空文件）*", ""])


def build() -> str:
    lines = [
        "# 源石与神灵·Codex 写作记忆汇编",
        "",
        "> 本文件由 `build_codex_markdown.py` 自动生成，完整汇集项目 `.codex` 中的文本内容。",
        "> 原始 skill 和 memory 文件保持不变；请不要直接编辑本汇编，否则重新生成时会被覆盖。",
        "",
        "## 目录",
        "",
        "- [项目写作 Skill](#项目写作-skill)",
        "- [Skill 方法与模板](#skill-方法与模板)",
        "- [整书写作记忆](#整书写作记忆)",
        "- [人物记忆](#人物记忆)",
        "- [分卷与逐章记忆](#分卷与逐章记忆)",
        "- [Skill 配置](#skill-配置)",
        "",
        "## 项目写作 Skill",
        "",
    ]
    append_markdown(lines, SKILL / "SKILL.md", "write-yuanshi-novel", 3)

    lines.extend(["## Skill 方法与模板", ""])
    for name in REFERENCE_ORDER:
        path = SKILL / "references" / name
        append_markdown(lines, path, path.stem, 3)

    lines.extend(["## 整书写作记忆", ""])
    append_markdown(lines, MEMORY / "整本书总纲.md", "《源石与神灵》整本书总纲", 3)

    lines.extend(["## 人物记忆", ""])
    for path in sorted((MEMORY / "人物").glob("*.md"), key=lambda item: item.name.casefold()):
        append_markdown(lines, path, path.stem, 3)

    lines.extend(["## 分卷与逐章记忆", ""])
    for volume in VOLUMES:
        volume_dir = MEMORY / volume
        lines.extend([f"### {volume}", ""])
        outline = volume_dir / "卷总纲.md"
        if outline.exists():
            append_markdown(lines, outline, "卷总纲", 4)
        chapters = sorted(
            (path for path in volume_dir.glob("*.md") if path.name != "卷总纲.md"),
            key=natural_key,
        )
        for path in chapters:
            append_markdown(lines, path, path.stem, 4)

    config = SKILL / "agents" / "openai.yaml"
    lines.extend([
        "## Skill 配置",
        "",
        f"> 来源：`{rel(config)}`",
        "",
        "```yaml",
        read(config),
        "```",
        "",
    ])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"已生成：{OUTPUT}")
