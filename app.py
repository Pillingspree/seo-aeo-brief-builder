"""Web app. Run locally with:  streamlit run app.py"""

import os

import streamlit as st

from briefbuilder.agent import brief_to_markdown, generate_brief

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

st.set_page_config(page_title="SEO + AEO Brief Builder", page_icon="🧭", layout="wide")

# ---- Optional password gate -------------------------------------------------
# If you set an APP_PASSWORD environment variable (for example on Render), the
# app asks for it before doing anything. This stops strangers from running up
# your AI bill. If it is not set, the app is open.
password = os.getenv("APP_PASSWORD")
if password:
    if not st.session_state.get("unlocked"):
        entered = st.text_input("Password", type="password")
        if entered and entered == password:
            st.session_state["unlocked"] = True
            st.rerun()
        elif entered:
            st.error("Wrong password.")
        st.stop()

st.title("🧭 SEO + AEO Content Brief Builder")
st.caption("Keyword in. Outline, FAQs, competitor gaps and a citation-ready answer out.")

with st.sidebar:
    st.header("Settings")
    mock = st.checkbox("Mock mode (free sample, no API key)", value=not os.getenv("ANTHROPIC_API_KEY"))
    st.caption("Real mode searches the live web, so a brief takes about a minute and costs a few cents.")

keyword = st.text_input("Target keyword", placeholder="e.g. answer engine optimization for agencies")
audience = st.text_input("Audience (optional)", placeholder="e.g. marketing agency owners")
notes = st.text_area(
    "Your own competitor notes (optional)",
    help="Paste notes about competitor pages to skip the live web search.",
    height=120,
)

if st.button("Build brief", type="primary"):
    try:
        with st.spinner("Researching and building the brief..."):
            st.session_state["brief"] = generate_brief(keyword, audience, notes, mock)
    except Exception as e:  # show a readable message instead of a crash
        st.error(str(e))

brief = st.session_state.get("brief")
if brief:
    st.success(f"Brief ready. Research source: {brief['research_source']}")
    if "verify" in brief["research_source"] or "mock" in brief["research_source"]:
        st.warning("These notes are not from live research. Verify facts before publishing.")

    overview, outline, faqs, gaps, answer, aeo = st.tabs(
        ["Overview", "Outline", "FAQs", "Competitor gaps", "Citation-ready answer", "AEO checklist"]
    )
    with overview:
        st.subheader("Search intent")
        st.write(brief["search_intent"])
        st.subheader("Title options")
        for t in brief["title_options"]:
            st.write(f"- {t}")
        st.write(f"**Meta description:** {brief['meta_description']}")
        st.write(f"**Target length:** about {brief['target_word_count']} words")
        st.write("**Secondary keywords:** " + ", ".join(brief["secondary_keywords"]))
        st.write("**Entities to mention:** " + ", ".join(brief["entities"]))
    with outline:
        for s in brief["outline"]:
            indent = "&nbsp;" * 6 * (int(s.get("level", 2)) - 2)
            st.markdown(f"{indent}**H{s.get('level', 2)}: {s.get('heading', '')}** (~{s.get('word_count', '?')} words)", unsafe_allow_html=True)
            st.caption(s.get("notes", ""))
    with faqs:
        for f in brief["faqs"]:
            with st.expander(f.get("question", "")):
                st.write(f.get("answer", ""))
    with gaps:
        for g in brief["competitor_gaps"]:
            st.markdown(f"**{g.get('gap', '')}**")
            st.write(f"Opportunity: {g.get('opportunity', '')}")
    with answer:
        st.info(brief["citation_ready_answer"])
        st.caption(f"{len(brief['citation_ready_answer'].split())} words. Aim for 40 to 60.")
        st.write("**Schema suggestion:** " + brief["schema_suggestion"])
    with aeo:
        for item in brief["aeo_checklist"]:
            st.checkbox(item, key=f"aeo_{item}")

    st.download_button("Download brief (.md)", brief_to_markdown(brief), file_name="content-brief.md")
