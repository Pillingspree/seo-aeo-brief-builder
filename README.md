# 🧭 SEO + AEO Content Brief Builder

Enter a keyword. Get a complete **content brief** a writer can follow, built for both classic SEO and **AEO** (answer engine optimization: being quoted by AI answer engines and search snippets).

## What each brief contains

- Search intent and title options
- Meta description, secondary keywords, entities to mention
- Section-by-section outline with word counts
- FAQs with standalone answers
- **Competitor gaps** and how to beat them
- A **citation-ready answer** (40-60 words, self-contained, quotable)
- AEO checklist and schema suggestion
- A label showing where the research came from (live web search, your notes, or model knowledge)

## How the agent works

1. **Research**: searches the web for the keyword and reads what the top pages cover (or uses competitor notes you paste in).
2. **Analyze**: asks Claude for a structured brief based on that research.
3. **Clean up**: validates the reply, fills any gaps, and labels the research source.

## Quick start

```bash
git clone https://github.com/<your-username>/seo-aeo-brief-builder.git
cd seo-aeo-brief-builder
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

Free sample (no API key):

```bash
python -m briefbuilder "answer engine optimization" --mock
streamlit run app.py
```

Real research (needs an Anthropic API key):

```bash
cp .env.example .env              # add your key
python -m briefbuilder "answer engine optimization" --audience "agency owners"
```

## Deploy on Render

A `render.yaml` is included. Set `ANTHROPIC_API_KEY` and `APP_PASSWORD` in Render's environment settings. See the guide in the repository description.

## Tests

```bash
python -m pytest
```

## Limitations

- AI-written briefs are a strong first draft, not a finished strategy. Verify facts and statistics before publishing.
- Live search quality depends on the search tool; the app labels the research source so you can tell.

## License

MIT
