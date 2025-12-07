# app.py
"""
Professional Profile Match Bot (Streamlit)
- Terminal & dashboard friendly
- Saves structured JSON as <username>.json in ./profiles/
- Designed so most answers are structured (select/multiselect/controlled format)
- Skills & Hobbies include a large catalog + search filter for quick selection
- Past notable projects require a short structured entry: "Title | Role | 1-line summary"
- Refer the user by name in prompts when available
- Use this with: pip install streamlit
- Run: streamlit run app.py --server.port $PORT --server.headless true
"""

import streamlit as st
import json
import os
import datetime
from typing import List

st.set_page_config(page_title="Professional Profile Match Bot", page_icon="🧑‍💼", layout="centered")

# -------------------------
# Catalogs (extended lists)
# -------------------------
SKILL_CATALOG = [
    # programming & data
    "Python", "Java", "C++", "C", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin",
    "SQL", "NoSQL", "PostgreSQL", "MySQL", "MongoDB",
    "Pandas", "NumPy", "SciPy", "Scikit-Learn", "TensorFlow", "PyTorch", "Keras",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Data Engineering", "ETL", "Airflow", "Spark",
    # web & infra
    "React", "Vue", "Angular", "Django", "Flask", "FastAPI", "Node.js",
    "Docker", "Kubernetes", "CI/CD", "Git", "GitHub Actions",
    "AWS", "GCP", "Azure", "Terraform", "Serverless",
    # product & design
    "UI/UX Design", "Figma", "Product Management", "A/B Testing",
    # business & others
    "SQLAlchemy", "Jenkins", "Linux", "Windows Server", "Cybersecurity",
    "Project Management", "Agile", "Scrum", "Finance Analysis",
    "Marketing", "SEO", "Public Speaking", "Sales", "Business Development",
    # soft skills
    "Leadership", "Mentoring", "Collaboration", "Critical Thinking",
    "Communication", "Presentation", "Negotiation"
]

HOBBY_CATALOG = [
    "Photography", "Videography", "Traveling", "Hiking", "Cycling", "Running",
    "Gaming", "Reading", "Writing", "Blogging", "Podcasting", "Cooking",
    "Gardening", "Painting", "Drawing", "Music (instrument)", "Singing",
    "Dancing", "Yoga", "Meditation", "DIY", "Woodworking", "Knitting", "Chess",
    "Board Games", "Puzzles", "Robotics", "Electronics"
]

INDUSTRY_OPTIONS = [
    "Finance", "Fintech", "Healthcare", "Biotech", "SaaS", "E-commerce",
    "Education", "Media", "Entertainment", "Gaming", "Retail",
    "Energy", "Automotive", "Manufacturing", "Telecommunications", "Logistics"
]

PREFERRED_COLLAB_OPTIONS = ["Remote", "In-person", "Hybrid", "Flexible"]
PREFERRED_ROLES = ["Developer", "Designer", "Data Analyst", "Data Scientist", "ML Engineer",
                   "Project Lead", "Product Manager", "Researcher", "QA Engineer", "DevOps Engineer"]
LANGUAGE_OPTIONS = [
    "English", "Hindi", "Spanish", "French", "German", "Chinese (Mandarin)", "Japanese",
    "Korean", "Portuguese", "Arabic", "Russian", "Bengali", "Urdu", "Punjabi", "Gujarati"
]
CERTIFICATION_OPTIONS = [
    "AWS Certified", "GCP Certified", "Azure Certified", "PMP", "Scrum Master",
    "Certified Data Scientist", "TensorFlow Developer", "Cisco Certified", "MBA",
    "BTech / BE", "MTech / ME", "PhD", "Certificate in AI/ML", "Other"
]
CONTACT_METHODS = ["Email", "WhatsApp", "Slack", "LinkedIn Message", "Phone Call", "Telegram", "Signal"]
AVAILABILITY_TIMEFRAME = ["Mornings", "Afternoons", "Evenings", "Weekends", "Flexible", "As-needed"]

# -------------------------
# Question flow (structured)
# -------------------------
QUESTIONS = [
    # Basic identity
    {"key": "name", "text": "👋 Hi! What's your full name?", "type": "text"},
    {"key": "preferred_name", "text": "Nice to meet you, {name}! What should we call you (nickname)?", "type": "text", "optional": True},
    {"key": "age", "text": "How old are you, {preferred_name_or_name}?", "type": "number"},
    {"key": "location", "text": "Where are you currently based (City / Region)?", "type": "text"},

    # Roles & domain
    {"key": "role", "text": "Which best describes your current role, {preferred_name_or_name}?", "type": "select",
     "options": ["Student", "Employee", "Freelancer", "Founder", "Investor", "Mentor"]},
    {"key": "domain", "text": "What's your primary domain of work or study?", "type": "select",
     "options": ["Computer Science", "Biotech", "Fintech", "Design", "Healthcare", "Education", "Marketing", "Other"]},

    # Experience & industry
    {"key": "experience", "text": "How many years of professional experience do you have?", "type": "number"},
    {"key": "industry_experience", "text": "Select industries you've worked in (choose all that apply)", "type": "multiselect",
     "options": INDUSTRY_OPTIONS},

    # Skills (searchable catalog)
    {"key": "skills", "text": "Select your professional skills (use search box to filter and pick multiple). These will be used as structured tags.", "type": "searchable_multiselect",
     "options": SKILL_CATALOG, "min_selection": 1},

    # Preferred collaboration specifics
    {"key": "preferred_collaboration", "text": "Preferred collaboration type?", "type": "select", "options": PREFERRED_COLLAB_OPTIONS},
    {"key": "preferred_roles_in_projects", "text": "Preferred roles you'd like to take in projects (pick multiple).", "type": "multiselect",
     "options": PREFERRED_ROLES},

    # Availability & commitment
    {"key": "availability_timeframe", "text": "When are you usually available to collaborate?", "type": "multiselect", "options": AVAILABILITY_TIMEFRAME},
    {"key": "time_commitment_per_week", "text": "How many hours per week can you commit to projects/mentorship?", "type": "number", "min": 0, "max": 168},

    # Contact & links (structured)
    {"key": "email", "text": "What's your professional email (preferred contact)?", "type": "text"},
    {"key": "preferred_contact_method", "text": "Preferred contact method?", "type": "select", "options": CONTACT_METHODS},
    {"key": "linkedin", "text": "LinkedIn profile URL (separate from portfolio):", "type": "text"},
    {"key": "github", "text": "GitHub / GitLab URL (for code projects):", "type": "text"},
    {"key": "portfolio", "text": "Portfolio URL (if different from LinkedIn/GitHub):", "type": "text"},

    # Projects & profile enrichment (structured short entries)
    {"key": "past_projects", "text": "List up to 3 notable past projects. Use the format: Title | Role | One-line summary (<=120 chars). Enter one project per input box.", "type": "structured_projects", "max_projects": 3},

    # Languages / certifications / education
    {"key": "languages_spoken", "text": "Languages you speak (choose all that apply)", "type": "multiselect", "options": LANGUAGE_OPTIONS},
    {"key": "certifications", "text": "Select certifications/degrees you hold (choose all that apply)", "type": "multiselect", "options": CERTIFICATION_OPTIONS},

    # Offers / Needs (existing fields - structured)
    {"key": "offers", "text": "What can you offer the community? (select multiple)", "type": "multiselect",
     "options": ["Mentorship", "Code/Design", "Services", "Capital", "Datasets", "Distribution", "Facilities", "Research Support"]},
    {"key": "needs", "text": "What are you currently seeking? (Choose up to 3)", "type": "multiselect", "options": ["Collaborator", "Job", "Client", "Investor", "Advisor", "Pilot Site", "Co-Founder"], "max_selections": 3},

    # Interests & hobbies (searchable + multi)
    {"key": "interests_hobbies", "text": "Interests / Hobbies (use search to pick many). These help with personal matching (choose multiple).", "type": "searchable_multiselect", "options": HOBBY_CATALOG},

    # Final optional short narrative but constrained (single-line tags)
    {"key": "one_line_bio", "text": "Write a one-line professional tagline (<=120 chars) — keep it concise, no paragraphs (used as a short vector tag).", "type": "text", "max_length": 120, "optional": True},
]

# -------------------------
# Helpers
# -------------------------
def format_list(items):
    return ", ".join(items) if isinstance(items, list) else items

def safe_filename(name: str) -> str:
    safe = (name or "user").strip().lower().replace(" ", "_")
    return safe if safe else "user"

def searchable_multiselect_widget(label: str, options: List[str], key: str, min_selection: int = 0):
    """
    Provide a search box and a multiselect that filters options by search term.
    Returns the selected list.
    """
    search = st.text_input(f"Search {label} (type to filter)", key=f"{key}_search")
    filtered = [o for o in options if search.strip().lower() in o.lower()] if search.strip() else options
    return st.multiselect(label, filtered, key=key)

# -------------------------
# Session state init
# -------------------------
if "responses" not in st.session_state:
    st.session_state["responses"] = {}
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "completed" not in st.session_state:
    st.session_state["completed"] = False

# If step overflows, mark completed
if st.session_state["step"] >= len(QUESTIONS):
    st.session_state["completed"] = True

# Header
st.markdown("<h1 style='text-align: center; color: #0b4a6f;'>Professional Profile Match Bot</h1>", unsafe_allow_html=True)
subtitle = "<p style='text-align: center;'>Answer structured questions — we use tags and controlled fields so your responses are ready for similarity search.</p>"
st.markdown(subtitle, unsafe_allow_html=True)
st.markdown("---")

# Main flow
if not st.session_state["completed"]:
    q = QUESTIONS[st.session_state["step"]]
    # Prepare dynamic name formatting
    resp = st.session_state["responses"]
    preferred_name_or_name = resp.get("preferred_name") or resp.get("name") or "there"
    text = q["text"].replace("{name}", resp.get("name", "there")).replace("{preferred_name_or_name}", preferred_name_or_name)

    st.subheader(text)

    key = q["key"]
    qtype = q["type"]

    # Render input types
    if qtype == "text":
        max_length = q.get("max_length", None)
        default = resp.get(key, "")
        val = st.text_input("Enter answer", value=default, key=f"input_{st.session_state['step']}")
        if max_length and val and len(val) > max_length:
            st.warning(f"Please keep this within {max_length} characters.")
        if st.button("Next", key=f"btn_next_text_{st.session_state['step']}"):
            if val.strip() == "" and not q.get("optional", False):
                st.warning("This field is required.")
            else:
                # trim to max_length if specified
                if max_length:
                    val = val.strip()[:max_length]
                st.session_state["responses"][key] = val.strip()
                st.session_state["step"] += 1
                st.experimental_rerun()

    elif qtype == "number":
        min_val = q.get("min", 0)
        max_val = q.get("max", 100)
        default = resp.get(key, min_val)
        try:
            val = st.number_input("Enter number", min_value=min_val, max_value=max_val, value=int(default), key=f"input_{st.session_state['step']}")
        except Exception:
            val = st.number_input("Enter number", min_value=min_val, max_value=max_val, key=f"input_{st.session_state['step']}")
        if st.button("Next", key=f"btn_next_num_{st.session_state['step']}"):
            st.session_state["responses"][key] = int(val)
            st.session_state["step"] += 1
            st.experimental_rerun()

    elif qtype == "select":
        options = q["options"]
        default = resp.get(key, options[0] if options else None)
        val = st.selectbox("Choose one:", options, index=options.index(default) if default in options else 0, key=f"input_{st.session_state['step']}")
        if st.button("Next", key=f"btn_next_sel_{st.session_state['step']}"):
            st.session_state["responses"][key] = val
            st.session_state["step"] += 1
            st.experimental_rerun()

    elif qtype == "multiselect":
        options = q["options"]
        default = resp.get(key, [])
        val = st.multiselect("Select option(s):", options, default=default, key=f"input_{st.session_state['step']}")
        if st.button("Next", key=f"btn_next_multi_{st.session_state['step']}"):
            max_sel = q.get("max_selections", None)
            if max_sel and len(val) > max_sel:
                st.warning(f"Maximum {max_sel} options allowed. Please adjust your selection.")
            elif q.get("min_selection") and len(val) < q.get("min_selection"):
                st.warning(f"Please select at least {q.get('min_selection')} option(s).")
            elif len(val) == 0 and q.get("min_selection", 0) > 0:
                st.warning("Please select at least one option.")
            else:
                st.session_state["responses"][key] = val
                st.session_state["step"] += 1
                st.experimental_rerun()

    elif qtype == "searchable_multiselect":
        options = q["options"]
        default = resp.get(key, [])
        # helper widget
        val = searchable_multiselect_widget("Select option(s):", options, key=f"input_{st.session_state['step']}", )
        # if nothing chosen but default exists, show it as selection (so user can keep it)
        if not val and default:
            val = default
        if st.button("Next", key=f"btn_next_search_multi_{st.session_state['step']}"):
            if q.get("min_selection") and len(val) < q.get("min_selection"):
                st.warning(f"Please select at least {q.get('min_selection')} option(s).")
            else:
                st.session_state["responses"][key] = val
                st.session_state["step"] += 1
                st.experimental_rerun()

    elif qtype == "structured_projects":
        max_projects = q.get("max_projects", 3)
        existing = resp.get(key, [])
        st.markdown("Enter up to **{0}** projects, one per box. **Format (required):** `Title | Role | One-line summary (<=120 chars)`".format(max_projects))
        projects = []
        for i in range(max_projects):
            default_val = existing[i] if i < len(existing) else ""
            p = st.text_input(f"Project {i+1}", value=default_val, key=f"proj_{st.session_state['step']}_{i}")
            projects.append(p)
        if st.button("Next", key=f"btn_next_projects_{st.session_state['step']}"):
            # filter out empties
            cleaned = [p.strip() for p in projects if p and p.strip()]
            # validate format
            invalid = []
            for p in cleaned:
                parts = [x.strip() for x in p.split("|")]
                if len(parts) != 3 or len(parts[2]) > 120 or parts[0] == "" or parts[1] == "":
                    invalid.append(p)
            if invalid:
                st.warning("One or more entries are invalid. Ensure format: Title | Role | One-line summary (<=120 chars).")
            else:
                st.session_state["responses"][key] = cleaned
                st.session_state["step"] += 1
                st.experimental_rerun()

    else:
        st.info("Unsupported question type.")
        if st.button("Skip"):
            st.session_state["step"] += 1
            st.experimental_rerun()

else:
    # Completed summary & save
    responses = st.session_state["responses"]
    display_name = responses.get("preferred_name") or responses.get("name") or "User"
    st.markdown(f"<h2 style='color: #0b6f44;'>Thank you, {display_name}! Your structured profile is ready.</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Quick structured summary (fields are stored as tags/arrays where applicable):")

    # Build summary layout
    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown(f"**Name:** {responses.get('name', 'N/A')}")
        st.markdown(f"**Preferred name:** {responses.get('preferred_name', 'N/A')}")
        st.markdown(f"**Age:** {responses.get('age', 'N/A')}")
        st.markdown(f"**Location:** {responses.get('location', 'N/A')}")
        st.markdown(f"**Role:** {responses.get('role', 'N/A')}")
        st.markdown(f"**Domain:** {responses.get('domain', 'N/A')}")
        st.markdown(f"**Experience (yrs):** {responses.get('experience', 'N/A')}")
        st.markdown(f"**Industries:** {format_list(responses.get('industry_experience', []))}")
        st.markdown(f"**Skills (tags):** {format_list(responses.get('skills', []))}")

    with right_col:
        st.markdown(f"**Preferred collaboration:** {responses.get('preferred_collaboration', 'N/A')}")
        st.markdown(f"**Preferred roles in projects:** {format_list(responses.get('preferred_roles_in_projects', []))}")
        st.markdown(f"**Availability timeframe:** {format_list(responses.get('availability_timeframe', []))}")
        st.markdown(f"**Hours/week available:** {responses.get('time_commitment_per_week', 'N/A')}")
        st.markdown(f"**Contact (email):** {responses.get('email', 'N/A')}")
        st.markdown(f"**Preferred contact method:** {responses.get('preferred_contact_method', 'N/A')}")
        st.markdown(f"**LinkedIn:** {responses.get('linkedin', 'N/A')}")
        st.markdown(f"**GitHub/GitLab:** {responses.get('github', 'N/A')}")
        st.markdown(f"**Portfolio:** {responses.get('portfolio', 'N/A')}")

    st.markdown("### Past notable projects (structured entries)")
    proj_list = responses.get("past_projects", [])
    if proj_list:
        for p in proj_list:
            parts = [x.strip() for x in p.split("|")]
            st.markdown(f"- **{parts[0]}** — *{parts[1]}* — {parts[2]}")
    else:
        st.markdown("No projects provided.")

    st.markdown("### Languages / Certifications / Interests")
    st.markdown(f"**Languages:** {format_list(responses.get('languages_spoken', []))}")
    st.markdown(f"**Certifications / Degrees:** {format_list(responses.get('certifications', []))}")
    st.markdown(f"**Offers:** {format_list(responses.get('offers', []))}")
    st.markdown(f"**Needs:** {format_list(responses.get('needs', []))}")
    st.markdown(f"**Interests / Hobbies:** {format_list(responses.get('interests_hobbies', []))}")
    st.markdown(f"**One-line bio (tag):** {responses.get('one_line_bio', 'N/A')}")

    # Save JSON file in profiles/
    folder = os.path.join(os.getcwd(), "profiles")
    os.makedirs(folder, exist_ok=True)
    filename = f"{safe_filename(responses.get('name'))}.json"
    file_path = os.path.join(folder, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(responses, f, indent=4, ensure_ascii=False)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"Your profile data has been saved as **{filename}** in the server folder `profiles/`.")
        st.info(f"Absolute server path: `{file_path}`")
        print(f"DEBUG: User profile saved to {file_path} at {ts}")
    except Exception as e:
        st.error(f"Failed to save profile: {e}")
        print(f"ERROR saving profile: {e}")

    # Download button for local persistence
    try:
        json_bytes = json.dumps(responses, indent=4, ensure_ascii=False).encode("utf-8")
        st.download_button(label="Download profile JSON", data=json_bytes, file_name=filename, mime="application/json")
    except Exception as e:
        st.warning("Download button failed: " + str(e))

    # Reset option
    if st.button("Create / Edit another profile"):
        st.session_state["responses"] = {}
        st.session_state["step"] = 0
        st.session_state["completed"] = False
        st.experimental_rerun()
