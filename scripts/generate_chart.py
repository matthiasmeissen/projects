import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
JSON_FILE = SCRIPT_DIR.parent / "projects.json"
README_FILE = SCRIPT_DIR.parent / "README.md"
OVERALL_SCALE = 10
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


def auto_scale(max_count):
    if max_count <= 0:
        return 1
    return max(1, math.ceil(max_count / MAX_BAR_WIDTH))


def load_projects():
    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    return data.get("projects", {})


def render_rows(rows, scale):
    if not rows:
        return "", ""
    max_label_len = max(len(label) for label, _ in rows)
    lines = [
        f"{label:<{max_label_len}} : {generate_bar(count, scale, MAX_BAR_WIDTH)} ({count})"
        for label, count in rows
    ]
    subtitle = f"_Each █ ≈ {scale} {'activity' if scale == 1 else 'activities'}._"
    return subtitle, "\n".join(lines)


def render_overall(projects):
    rows = [
        (details.get("name", slug), len(details.get("activities", [])))
        for slug, details in projects.items()
    ]
    rows.sort(key=lambda r: r[1], reverse=True)
    return render_rows(rows, OVERALL_SCALE)


def render_by_category(projects):
    totals = Counter()
    for details in projects.values():
        cat = details.get("category", "uncategorized")
        totals[cat] += len(details.get("activities", []))
    rows = sorted(totals.items(), key=lambda r: r[1], reverse=True)
    scale = auto_scale(max((c for _, c in rows), default=0))
    return render_rows(rows, scale)


def render_by_tag(projects):
    totals = Counter()
    for details in projects.values():
        count = len(details.get("activities", []))
        for tag in details.get("tags", []):
            totals[tag] += count
    rows = sorted(totals.items(), key=lambda r: (-r[1], r[0]))
    scale = auto_scale(max((c for _, c in rows), default=0))
    return render_rows(rows, scale)


def render_by_year(projects):
    totals = Counter()
    for details in projects.values():
        for activity in details.get("activities", []):
            iso = activity.get("date")
            if not iso:
                continue
            year = date.fromisoformat(iso).year
            totals[year] += 1
    current_year = date.today().year
    rows = [
        (f"{year} (YTD)" if year == current_year else str(year), count)
        for year, count in sorted(totals.items())
    ]
    scale = auto_scale(max((c for _, c in rows), default=0))
    return render_rows(rows, scale)


CHARTS = {
    "overall": render_overall,
    "by-category": render_by_category,
    "by-tag": render_by_tag,
    "by-year": render_by_year,
}


def replace_section(readme_text, chart_id, subtitle, body):
    pattern = re.compile(
        rf"(<!-- chart:{re.escape(chart_id)} -->)(.*?)(<!-- /chart:{re.escape(chart_id)} -->)",
        re.DOTALL,
    )
    replacement = f"\\1\n{subtitle}\n```\n{body}\n```\n\\3"
    new_text, n = pattern.subn(replacement, readme_text)
    return new_text, n > 0


def main():
    projects = load_projects()
    if not projects:
        print("No projects found.")
        return

    readme = README_FILE.read_text(encoding="utf-8")
    updated = readme
    for chart_id, renderer in CHARTS.items():
        subtitle, body = renderer(projects)
        if not body:
            print(f"skipped: {chart_id} (no data)")
            continue
        new_text, found = replace_section(updated, chart_id, subtitle, body)
        if not found:
            print(f"skipped: {chart_id} (marker not found)")
            continue
        updated = new_text
        print(f"Updated section: {chart_id}")

    if updated == readme:
        print("README.md already up to date.")
        return

    README_FILE.write_text(updated, encoding="utf-8")
    print(f"Wrote {README_FILE}")


if __name__ == "__main__":
    main()
