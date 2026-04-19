import json
import math
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
JSON_FILE = SCRIPT_DIR.parent / "projects.json"
README_FILE = SCRIPT_DIR.parent / "README.md"
SCALE = 10
MAX_BAR_WIDTH = 60

FRACTIONAL_BLOCKS = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]


def generate_bar(count, scale, max_width):
    if count <= 0:
        return ""

    num_full_blocks = math.floor(count / scale)
    remainder = count % scale

    display_blocks = min(num_full_blocks, max_width)
    bar = "█" * display_blocks

    if display_blocks < max_width and remainder > 0 and FRACTIONAL_BLOCKS:
        fraction_index = math.ceil((remainder / scale) * (len(FRACTIONAL_BLOCKS) - 1))
        fraction_index = min(max(1, fraction_index), len(FRACTIONAL_BLOCKS) - 1)
        bar += FRACTIONAL_BLOCKS[fraction_index]

    return bar


def build_chart(projects):
    entries = []
    for key, details in projects.items():
        name = details.get("name", key)
        activities = details.get("activities", [])
        count = len(activities) if isinstance(activities, list) else 0
        entries.append({"name": name, "count": count})

    entries.sort(key=lambda x: x["count"], reverse=True)
    max_name_len = max((len(e["name"]) for e in entries), default=0)

    lines = []
    for e in entries:
        bar = generate_bar(e["count"], SCALE, MAX_BAR_WIDTH)
        lines.append(f"{e['name']:<{max_name_len}} : {bar} ({e['count']})")
    return "\n".join(lines)


def replace_first_code_block(readme_text, new_body):
    pattern = re.compile(r"(^|\n)(```[^\n]*\n)(.*?)(\n```)", re.DOTALL)
    match = pattern.search(readme_text)
    if not match:
        raise RuntimeError("No fenced code block found in README.md")
    start, end = match.span(3)
    return readme_text[:start] + new_body + readme_text[end:]


def main():
    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    projects = data.get("projects", {})
    if not projects:
        print("No projects found in the JSON data.")
        return

    chart = build_chart(projects)
    readme = README_FILE.read_text(encoding="utf-8")
    updated = replace_first_code_block(readme, chart)

    if updated == readme:
        print("README.md already up to date.")
        return

    README_FILE.write_text(updated, encoding="utf-8")
    print(f"Updated chart in {README_FILE}")


if __name__ == "__main__":
    main()
