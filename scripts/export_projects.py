#!/usr/bin/env python3
"""
Generate Obsidian-compatible project markdown files from projects.json.

Reads:  projects.json (same directory by default, or path as first arg)
Writes: /Users/matthiasmeissen/dev/garden/projects/<slug>.md
        (or path as second arg)

Each project in the JSON becomes one markdown file with YAML frontmatter
containing type, category, tags, and reference — ready for the garden vault.

Tag cleanup is applied via TAG_DROP (removed entirely) and TAG_RENAME
(normalized to canonical form). Edit those sets to tune the vocabulary.
"""

import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Tag normalization
# --------------------------------------------------------------------------

# projects.json is the cleaned source of truth; these renames are a safety
# net for future typos/casing variants only.
TAG_RENAME = {
    "threejs": "three-js",
    "three.js": "three-js",
    "modular": "modular-synth",
    "pen-plotter": "plotter",
    "3dprinting": "3d-printing",
}

# --------------------------------------------------------------------------
# File generation
# --------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert a project name to a kebab-case filename."""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)   # strip punctuation
    s = re.sub(r"[\s_]+", "-", s)    # whitespace -> hyphen
    s = re.sub(r"-+", "-", s)        # collapse repeated hyphens
    return s.strip("-")

def clean_tags(tags: list[str]) -> list[str]:
    """Apply rename rules, preserving order and deduplicating."""
    out, seen = [], set()
    for t in tags:
        t = TAG_RENAME.get(t, t)
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out

def format_reference(ref) -> str:
    """Format the reference field — scalar or list."""
    if isinstance(ref, list):
        return "reference:\n" + "\n".join(f"  - {r}" for r in ref)
    return f"reference: {ref}"

def render_markdown(project: dict) -> str:
    """Render one project entry as a markdown file with YAML frontmatter."""
    name = project["name"]
    description = project.get("description", "").rstrip(".")
    type_ = project.get("type", "practice")
    category = project.get("category", "computation")
    tags = clean_tags(project.get("tags", []))
    reference = project.get("reference", "")

    tag_str = "[" + ", ".join(tags) + "]"
    body = f"{description}." if description else ""

    return f"""---
type: {type_}
category: {category}
tags: {tag_str}
{format_reference(reference)}
---

# {name}

{body}

## Related concepts

<!-- Wiki-link concept notes here as they grow, e.g. [[ladder-filter]] -->
"""

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("projects.json")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/Users/matthiasmeissen/dev/garden/projects")

    if not src.exists():
        sys.exit(f"Source not found: {src}")

    data = json.loads(src.read_text(encoding="utf-8"))
    raw = data if isinstance(data, list) else data.get("projects", {})
    projects = list(raw.values()) if isinstance(raw, dict) else raw

    dst.mkdir(parents=True, exist_ok=True)

    # Tag audit — helps you spot what the vocabulary actually contains
    all_tags: dict[str, int] = {}
    for p in projects:
        for t in clean_tags(p.get("tags", [])):
            all_tags[t] = all_tags.get(t, 0) + 1

    # Write one file per project; detect slug collisions up front
    seen_slugs: dict[str, str] = {}
    for p in projects:
        slug = slugify(p["name"])
        if slug in seen_slugs:
            sys.exit(f"Slug collision: '{slug}' from '{p['name']}' and '{seen_slugs[slug]}'")
        seen_slugs[slug] = p["name"]
        (dst / f"{slug}.md").write_text(render_markdown(p), encoding="utf-8")

    # Write a README in the projects folder
    readme = """# Projects

All active practices and one-off projects as graph-navigable nodes.

## How to use

Link to any project from a concept note using `[[project-slug]]`. Obsidian's graph and backlinks pane will surface the connections.

## Schema

- **type** — `practice` (ongoing ritual, series, playground) or `project` (self-contained, one-off)
- **category** — `computation` (keyboard work), `making` (hands on material), or `device` (both — own hardware + firmware)
- **tags** — domain + tool + format vocabulary, all lowercase kebab-case

## Source of truth

Canonical project data lives in `github.com/matthiasmeissen/projects/projects.json`. These markdown files are regenerated from it via `export_projects.py`.
"""
    (dst / "README.md").write_text(readme)

    # Report
    print(f"Wrote {len(projects)} project files to {dst}/")
    print(f"\nTag vocabulary ({len(all_tags)} unique, sorted by frequency):")
    for tag, count in sorted(all_tags.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {count:3d}  {tag}")

if __name__ == "__main__":
    main()