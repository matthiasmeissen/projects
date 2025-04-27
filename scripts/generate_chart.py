import json
import math

# --- Configuration ---
JSON_FILE = '../projects.json'
SCALE = 10  # How many activities each full block represents
MAX_BAR_WIDTH = 60  # Maximum number of characters for the bar
OUTPUT_FILE = None # Set to a filename like 'chart.md' to write to a file, None to print to console
# --- End Configuration ---

# Characters for fractional blocks (optional, set to "" for none)
# Represents 1/10th increments up to 9/10ths
FRACTIONAL_BLOCKS = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
# Or use just a single character for any fraction:
# FRACTIONAL_BLOCKS = ["", "▌", "▌", "▌", "▌", "▌", "▌", "▌"]


def generate_bar(count, scale, max_width):
    """Generates the text bar string for a given count."""
    if count <= 0:
        return ""

    full_blocks_exact = count / scale
    num_full_blocks = math.floor(full_blocks_exact)
    remainder = count % scale

    # Apply max width limit
    display_blocks = min(num_full_blocks, max_width)
    bar = "█" * display_blocks

    # Add fractional block if needed and space permits
    if display_blocks < max_width and remainder > 0 and FRACTIONAL_BLOCKS:
         # Calculate index for fractional blocks (adjusting for scale)
        fraction_index = math.ceil((remainder / scale) * (len(FRACTIONAL_BLOCKS) -1))
        # Ensure index is valid
        fraction_index = min(max(1, fraction_index), len(FRACTIONAL_BLOCKS) - 1)
        bar += FRACTIONAL_BLOCKS[fraction_index]
    elif num_full_blocks > max_width:
        # Indicate truncation if bar was capped
        # You could add a specific character like '>' or '...'
        pass # Keep it simple for now

    return bar

def main():
    """Reads JSON, processes data, and generates Markdown."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at '{JSON_FILE}'")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{JSON_FILE}'")
        return

    projects = data.get('projects', {})
    if not projects:
        print("No projects found in the JSON data.")
        return

    project_activities = []
    for key, details in projects.items():
        name = details.get('name', key) # Use key as fallback name
        activities = details.get('activities', [])
        count = len(activities) if isinstance(activities, list) else 0
        project_activities.append({'name': name, 'count': count})

    # Sort projects by activity count descending
    project_activities.sort(key=lambda x: x['count'], reverse=True)

    # Find max name length for alignment
    max_name_len = 0
    if project_activities:
        max_name_len = max(len(p['name']) for p in project_activities)

    # --- Generate Markdown Output ---
    markdown_lines = []
    markdown_lines.append("# Project Activity - Visualized")
    markdown_lines.append("")
    markdown_lines.append(f"Each `█` represents approximately **{SCALE}** activities. Maximum bar length: **{MAX_BAR_WIDTH}** characters.")
    markdown_lines.append("")
    markdown_lines.append("```text")

    for project in project_activities:
        name = project['name']
        count = project['count']
        bar = generate_bar(count, SCALE, MAX_BAR_WIDTH)
        # Format: Name (left-aligned) : Bar (Count)
        line = f"{name:<{max_name_len}} : {bar} ({count})"
        markdown_lines.append(line)

    markdown_lines.append("```")
    markdown_lines.append(f"\n*(Generated from `{JSON_FILE}`)*")

    # --- Output ---
    final_markdown = "\n".join(markdown_lines)

    if OUTPUT_FILE:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(final_markdown)
            print(f"Markdown chart successfully written to '{OUTPUT_FILE}'")
        except IOError as e:
            print(f"Error writing to file '{OUTPUT_FILE}': {e}")
    else:
        print(final_markdown)

if __name__ == "__main__":
    main()