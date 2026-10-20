"""The brief-building agent: keyword in, complete content brief out.

An "agent" here just means a program that works through several steps on its
own. Ours has three:

  STEP 1  RESEARCH  Search the web for the keyword and read what the top pages
                    cover (or use competitor notes you paste in yourself).
  STEP 2  ANALYZE   Give those notes to Claude and ask for a structured brief:
                    outline, FAQs, competitor gaps, citation-ready answer.
  STEP 3  CLEAN UP  Check the AI's reply is valid, fill any missing pieces, and
                    label where the research came from, so nobody is misled.

Mock mode skips the AI entirely and returns a sample brief, so you can demo and
test for free.
"""

import json
import os

from .prompts import BRIEF_PROMPT, BRIEF_SYSTEM, RESEARCH_PROMPT, RESEARCH_SYSTEM

DEFAULT_MODEL = "claude-sonnet-5-5"

# Claude's built-in web search tool. The version name can change over time, so
# it is a setting you can override without editing code.
DEFAULT_SEARCH_TOOL = "web_search_20250305"

REQUIRED_KEYS = {
    "search_intent": "",
    "title_options": [],
    "meta_description": "",
    "target_word_count": 1500,
    "secondary_keywords": [],
    "entities": [],
    "outline": [],
    "faqs": [],
    "competitor_gaps": [],
    "citation_ready_answer": "",
    "aeo_checklist": [],
    "schema_suggestion": "",
}


def _client():
    # Imported here so mock mode and the tests work without the library.
    from anthropic import Anthropic

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to a .env file (see .env.example) "
            "or turn on mock mode to try the tool for free."
        )
    return Anthropic(api_key=key)


def _model() -> str:
    return os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)


def _text_of(response) -> str:
    """Join the text parts of a Claude reply (ignores search-tool blocks)."""
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()


# ---------------------------------------------------------------- STEP 1
def research_serp(keyword: str, audience: str) -> tuple[str, str]:
    """Search the live web and return (research_notes, source_label)."""
    client = _client()
    prompt = RESEARCH_PROMPT.format(keyword=keyword, audience=audience or "general readers")
    messages = [{"role": "user", "content": prompt}]
    tools = [
        {
            "type": os.getenv("SEARCH_TOOL_TYPE", DEFAULT_SEARCH_TOOL),
            "name": "web_search",
            "max_uses": 5,
        }
    ]
    try:
        response = client.messages.create(
            model=_model(), max_tokens=3000, system=RESEARCH_SYSTEM, messages=messages, tools=tools
        )
        # Long searches can pause; let the model continue a few times.
        for _ in range(3):
            if response.stop_reason != "pause_turn":
                break
            messages = messages + [{"role": "assistant", "content": response.content}]
            response = client.messages.create(
                model=_model(), max_tokens=3000, system=RESEARCH_SYSTEM, messages=messages, tools=tools
            )
        notes = _text_of(response)
        if notes:
            return notes, "live web search"
    except Exception as exc:  # search unavailable: fall back, but say so
        fallback_reason = str(exc)[:200]
    else:
        fallback_reason = "search returned no text"

    reply = client.messages.create(
        model=_model(),
        max_tokens=2000,
        system=RESEARCH_SYSTEM,
        messages=[{"role": "user", "content": prompt + "\nLive search is unavailable. Use general knowledge and say so."}],
    )
    return (
        f"(Live search failed: {fallback_reason}. These notes come from model knowledge. Verify before publishing.)\n"
        + _text_of(reply),
        "model knowledge (verify manually)",
    )


# ---------------------------------------------------------------- STEP 2
def build_brief(keyword: str, research: str, source: str, audience: str) -> dict:
    client = _client()
    prompt = BRIEF_PROMPT.format(
        keyword=keyword, audience=audience or "general readers", research=research, source=source
    )
    response = client.messages.create(
        model=_model(), max_tokens=4000, system=BRIEF_SYSTEM, messages=[{"role": "user", "content": prompt}]
    )
    return parse_brief_json(_text_of(response))


# ---------------------------------------------------------------- STEP 3
def parse_brief_json(raw: str) -> dict:
    """Pull the JSON object out of Claude's reply and fill in anything missing."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The AI reply did not contain a JSON brief. Please try again.")
    data = json.loads(raw[start : end + 1])
    for key, default in REQUIRED_KEYS.items():
        value = data.get(key)
        if value is None or not isinstance(value, type(default)):
            data[key] = default  # wrong type or missing: use a safe empty value
    return data


def mock_brief(keyword: str) -> dict:
    """A fixed sample brief for mock mode. No network, no cost."""
    kw = keyword.strip()
    return {
        "search_intent": f"Searchers for '{kw}' want a clear explanation and a practical first step.",
        "title_options": [f"{kw.title()}: A Practical Guide", f"What Is {kw.title()}?", f"{kw.title()} Explained Simply"],
        "meta_description": f"A clear, practical guide to {kw}: what it is, how it works and how to start.",
        "target_word_count": 1500,
        "secondary_keywords": [f"{kw} examples", f"{kw} for beginners", f"best {kw} tools", f"{kw} checklist"],
        "entities": ["Google Search", "AI answer engines", "schema.org"],
        "outline": [
            {"heading": f"What is {kw}? (direct answer)", "level": 2, "notes": "Answer in the first 60 words.", "word_count": 150},
            {"heading": "Why it matters", "level": 2, "notes": "Business impact. Needs source for any statistic.", "word_count": 200},
            {"heading": "How it works step by step", "level": 2, "notes": "Numbered steps with one example each.", "word_count": 400},
            {"heading": "Common mistakes", "level": 2, "notes": "Short list with fixes.", "word_count": 250},
            {"heading": "Frequently asked questions", "level": 2, "notes": "Use the FAQ list below, with FAQPage schema.", "word_count": 300},
        ],
        "faqs": [
            {"question": f"What is {kw}?", "answer": f"Mock answer: a short, standalone definition of {kw} goes here."},
            {"question": f"How do I get started with {kw}?", "answer": "Mock answer: the first practical step goes here."},
        ],
        "competitor_gaps": [
            {"gap": "Competitors bury the direct answer.", "opportunity": "Lead with a quotable answer block."},
            {"gap": "Few pages include real examples.", "opportunity": "Add one worked example per section."},
        ],
        "citation_ready_answer": (
            f"{kw.capitalize()} is the practice readers search for when they want a clear, practical answer "
            "before making a decision. A strong explanation defines the term in one sentence, shows why it "
            "matters, and gives the first step to take. This placeholder appears in mock mode only; real mode "
            "writes an answer grounded in current research."
        ),
        "aeo_checklist": [
            "Put the direct answer in the first paragraph.",
            "Use question-style H2 headings.",
            "Keep each FAQ answer self-contained.",
            "Add FAQPage schema.",
            "Cite named sources for every statistic.",
            "Add the author and a last-updated date.",
        ],
        "schema_suggestion": "Article plus FAQPage, so answer engines can read the questions and answers directly.",
    }


def generate_brief(
    keyword: str,
    audience: str = "",
    competitor_notes: str = "",
    mock: bool = False,
) -> dict:
    """Run the whole agent and return the finished brief as a dictionary."""
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("Please enter a keyword.")

    if mock:
        brief = mock_brief(keyword)
        brief.update(keyword=keyword, audience=audience or "general readers", research_source="mock (sample data)")
        return brief

    if competitor_notes.strip():
        research, source = competitor_notes.strip(), "competitor notes pasted by the user"
    else:
        research, source = research_serp(keyword, audience)

    brief = build_brief(keyword, research, source, audience)
    brief.update(keyword=keyword, audience=audience or "general readers", research_source=source)
    return brief


def brief_to_markdown(brief: dict) -> str:
    """Turn a brief into a clean document a writer can open and follow."""
    lines = [
        f"# Content Brief: {brief['keyword']}",
        "",
        f"**Audience:** {brief['audience']}  ",
        f"**Research source:** {brief['research_source']}  ",
        f"**Target length:** about {brief['target_word_count']} words",
        "",
        "## Search intent",
        brief["search_intent"],
        "",
        "## Title options",
        *[f"- {t}" for t in brief["title_options"]],
        "",
        f"**Meta description:** {brief['meta_description']}",
        "",
        "## Keywords and entities",
        "**Secondary keywords:** " + ", ".join(brief["secondary_keywords"]),
        "",
        "**Entities to mention:** " + ", ".join(brief["entities"]),
        "",
        "## Outline",
    ]
    for s in brief["outline"]:
        hashes = "#" * (int(s.get("level", 2)) + 1)
        lines += [f"{hashes} {s.get('heading', '')}", f"{s.get('notes', '')} (~{s.get('word_count', '?')} words)", ""]
    lines += ["## Citation-ready answer", f"> {brief['citation_ready_answer']}", "", "## FAQs"]
    for f in brief["faqs"]:
        lines += [f"**{f.get('question', '')}**", f.get("answer", ""), ""]
    lines += ["## Competitor gaps"]
    for g in brief["competitor_gaps"]:
        lines.append(f"- **{g.get('gap', '')}** → {g.get('opportunity', '')}")
    lines += ["", "## AEO checklist", *[f"- [ ] {c}" for c in brief["aeo_checklist"]], "", "## Schema", brief["schema_suggestion"], ""]
    return "\n".join(lines)
