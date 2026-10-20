"""Command-line interface.

Examples:
    python -m briefbuilder "content repurposing" --mock
    python -m briefbuilder "aeo for agencies" --audience "agency owners" --out briefs
"""

import argparse
import json
import os
import re

from .agent import brief_to_markdown, generate_brief


def main(argv: list[str] | None = None) -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(prog="briefbuilder", description="Keyword in, SEO + AEO content brief out.")
    parser.add_argument("keyword")
    parser.add_argument("--audience", default="")
    parser.add_argument("--notes-file", help="Text file with your own competitor notes (skips web search)")
    parser.add_argument("--out", default="output")
    parser.add_argument("--mock", action="store_true", help="No API key needed; sample brief")
    args = parser.parse_args(argv)

    notes = ""
    if args.notes_file:
        with open(args.notes_file, encoding="utf-8") as f:
            notes = f.read()

    brief = generate_brief(args.keyword, args.audience, notes, args.mock)
    os.makedirs(args.out, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", args.keyword.lower()).strip("-") or "brief"
    md_path = os.path.join(args.out, f"{slug}.md")
    json_path = os.path.join(args.out, f"{slug}.json")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(brief_to_markdown(brief))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)
    print("Saved", md_path)
    print("Saved", json_path)


if __name__ == "__main__":
    main()
