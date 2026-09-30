"""Rename a tag across all memo file pairs (.md + .json).

Replaces old tag with new tag in both the Markdown content (#old → #new)
and the JSON tags array (["old"] → ["new"]).

Usage:
    python rename_tag.py <old_tag> <new_tag> [--dry-run]

Examples:
    python rename_tag.py bak archive --dry-run
    python rename_tag.py bak archive
    python rename_tag.py hw huawei
"""

import argparse
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def rename_tag(old_tag: str, new_tag: str, dry_run: bool) -> None:
    old_tag = old_tag.lstrip("#")
    new_tag = new_tag.lstrip("#")

    # Match #old_tag as a whole word (not #old_tag_suffix)
    md_pattern = re.compile(rf"#({re.escape(old_tag)})(?![\w])")

    matched = []

    for filename in sorted(os.listdir(SCRIPT_DIR)):
        if not filename.endswith(".json"):
            continue

        json_path = os.path.join(SCRIPT_DIR, filename)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [skip] {filename}: {e}")
            continue

        tags = data.get("tags", [])
        if old_tag not in tags:
            continue

        uid = data.get("uid", filename.removesuffix(".json"))
        md_filename = f"{uid}.md"
        md_path = os.path.join(SCRIPT_DIR, md_filename)
        md_exists = os.path.exists(md_path)

        # --- Prepare JSON changes ---
        new_tags = [new_tag if t == old_tag else t for t in tags]
        new_json = json.dumps({**data, "tags": new_tags}, ensure_ascii=False, separators=(",", ":"))

        # --- Prepare MD changes ---
        md_old_content = ""
        md_new_content = ""
        md_replacements = 0
        if md_exists:
            with open(md_path, "r", encoding="utf-8") as f:
                md_old_content = f.read()
            md_new_content, md_replacements = md_pattern.subn(f"#{new_tag}", md_old_content)

        matched.append((json_path, md_path, filename, md_filename, md_exists,
                        data, new_json, md_old_content, md_new_content, md_replacements))

    if not matched:
        print(f"No memos found with tag '#{old_tag}'.")
        return

    print(f"Found {len(matched)} memo(s) with tag '#{old_tag}':\n")
    for json_path, md_path, json_name, md_name, md_exists, data, new_json, \
        md_old, md_new, md_reps in matched:
        tags_str = ", ".join(f"#{t}" for t in data.get("tags", []))
        print(f"  {json_name}" + (f" + {md_name}" if md_exists else "") + f"  [{tags_str}]")

        if dry_run:
            continue

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(new_json)
        print(f"    [json] tags: {data['tags']} -> {json.loads(new_json)['tags']}")

        # Write MD
        if md_exists and md_reps > 0:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_new)
            print(f"    [md]   {md_reps} replacement(s): #{old_tag} -> #{new_tag}")

    action = "Would rename" if dry_run else "Renamed"
    print(f"\n{action} #{old_tag} -> #{new_tag} in {len(matched)} pair(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename a tag across all memo .md + .json pairs.",
    )
    parser.add_argument("old_tag", help="Old tag to replace (without #), e.g. bak")
    parser.add_argument("new_tag", help="New tag name (without #), e.g. archive")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be changed, no actual modification.",
    )
    args = parser.parse_args()

    rename_tag(args.old_tag, args.new_tag, args.dry_run)


if __name__ == "__main__":
    main()
