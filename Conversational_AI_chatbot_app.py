import streamlit as st

st.set_page_config(
    page_title="AI Resume Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sqlite3
import spacy
from PyPDF2 import PdfReader
import re

# -----------------------------
# NLP setup (offline)
# -----------------------------
nlp = spacy.load("en_core_web_sm")

KNOWN_SKILLS = [
    "python", "sql", "tensorflow", "pytorch", "fastapi",
    "pandas", "numpy", "machine learning", "deep learning"
]

ADD_WORDS = ["add", "know", "learned", "experienced", "also know"]
REMOVE_WORDS = ["remove", "delete", "drop", "dont use", "do not use"]

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("resume.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    degree TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    skill TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

conn.commit()

# -----------------------------
# Resume parsing helpers
# -----------------------------
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def normalize_pdf_text(text):
    # Fix spaced characters: a r n a b -> arnab
    text = re.sub(r'(\w)\s+(?=\w)', r'\1', text)

    # Fix spaced email punctuation: @ . -
    text = text.replace(" @ ", "@").replace(" . ", ".").replace(" - ", "-")

    return text

def extract_resume_fields(text):
    data = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "education": [],
        "projects":[]
    }

    # Preprocesses text into lines once
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # -----------------------------
    # Email extraction
    # -----------------------------
    email_match = re.search(r"\b[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b", text)
    if email_match:
        data["email"] = re.sub(r"\s+", "", email_match.group(0))

    # -----------------------------
    # Phone extraction (supports +91, spaces, dashes)
    # -----------------------------
    phone_match = re.search(r"(\+?\d[\d\s\-]{8,}\d)", text)
    if phone_match:
        data["phone"] = re.sub(r"[^\d+]", "", phone_match.group(0))

    # -----------------------------
    # Name extraction using spaCy NER
    # -----------------------------
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            data["name"] = ent.text
            break
    # -----------------------------
    # Fallback if spaCy fails
    # -----------------------------
    if not data["name"] and lines:
        data["name"] = lines[0]

    # -----------------------------
    # Skill extraction (dictionary + dedupe)
    # -----------------------------
    lower_text = text.lower()
    found_skills = set()

    for skill in KNOWN_SKILLS:
        if skill in lower_text:
            found_skills.add(skill.capitalize())

    data["skills"] = list(found_skills)

    # -----------------------------
    # Education extraction
    # -----------------------------
    DEGREE_KEYWORDS = [
    "b.tech", "bachelor", "bsc", "msc", "m.tech",
    "master", "phd", "mba", "bca", "mca"
    ]

    for line in lines:
        lower_line = line.lower()
        for deg in DEGREE_KEYWORDS:
            if deg in lower_line:
                data["education"].append(line)
                break

    # -----------------------------
    # Project extraction
    # -----------------------------
    project_section = False

    SECTION_BREAKERS = ["education", "experience", "skills", "certifications"]

    for line in lines:
        lower_line = line.lower()
        
        # Detect project header
        if "project" in line.lower():
            project_section = True
            continue
        
        #Collect Project lines 
        if project_section:
            if any(word in lower_line for word in SECTION_BREAKERS):
                break
            data["projects"].append(line.strip())

    return data

# -----------------------------
# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "step" not in st.session_state:
    st.session_state.step = "menu"

if "user_data" not in st.session_state:
    st.session_state.user_data = {}

if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None

if "missing_fields" not in st.session_state:
    st.session_state.missing_fields = []

# -----------------------------
# Debug: show current step
# -----------------------------
with st.sidebar:
    st.write("Current step:", st.session_state.step)

# -----------------------------
# UI Title
# -----------------------------
st.title("AI Resume Chatbot")

# -----------------------------
# Display chat history
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# Helper functions
# -----------------------------
def get_user_by_email(email):
    cursor.execute("SELECT id, name FROM users WHERE email=?", (email,))
    return cursor.fetchone()


def get_user_skills(user_id):
    cursor.execute("SELECT skill FROM skills WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]


def add_skill(user_id, skill):
    existing = get_user_skills(user_id)
    if skill.lower() in [s.lower() for s in existing]:
        return False
    cursor.execute("INSERT INTO skills (user_id, skill) VALUES (?, ?)", (user_id, skill))
    conn.commit()
    return True


def remove_skill(user_id, skill):
    cursor.execute("DELETE FROM skills WHERE user_id=? AND LOWER(skill)=LOWER(?)", (user_id, skill))
    conn.commit()


def parse_skill_intent(text):
    doc = nlp(text.lower())
    found_skills = []

    for token in doc:
        if token.text in KNOWN_SKILLS:
            found_skills.append(token.text)

    intent = None
    for word in ADD_WORDS:
        if word in text.lower():
            intent = "add"
    for word in REMOVE_WORDS:
        if word in text.lower():
            intent = "remove"

    return intent, found_skills

# -----------------------------
# Bot logic
# -----------------------------
def bot_reply(user_input):
    step = st.session_state.step

    if step == "menu":
        if user_input == "1":
            st.session_state.step = "ask_name"
            return "What is your full name?"
        elif user_input == "2":
            st.session_state.step = "upload_resume"
            st.rerun()
        elif user_input == "3":
            st.session_state.step = "load_email"
            return "Please enter your email to load your profile."
        else:
            return "Please type 1 to create manually, 2 to upload resume, or 3 to edit existing."

    # ---------------- Resume Upload Flow ----------------
    elif step == "resume_extracted":
        if user_input.lower() == "yes":
            data = st.session_state.user_data

            cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)",
                           (data.get("name"), data.get("email"), data.get("phone")))
            user_id = cursor.lastrowid

            #save skills 
            for skill in data.get("skills", []):
                cursor.execute("INSERT INTO skills (user_id, skill) VALUES (?, ?)",
                               (user_id, skill))
                
            #save education
            for edu in data.get("education", []):
                cursor.execute("INSERT INTO education (user_id, degree) VALUES (?, ?)",
                                (user_id, edu))
                
            #save projects
            for proj in data.get("projects", []):
                cursor.execute("INSERT INTO projects (user_id, description) VALUES (?, ?)",
                                (user_id, proj))

            conn.commit()
            st.session_state.step = "menu"
            return "Resume saved successfully!"
        else:
            st.session_state.step = "menu"
            return "Upload cancelled."
        
    # ---------------- Missing Field Completion ----------------
    elif step == "ask_missing":
        if not st.session_state.missing_fields:
            st.session_state.step = "resume_extracted"
            return "All fields captured. Type YES to save."
        
        field = st.session_state.missing_fields[0]

        # Save the user's response into the correct field
        st.session_state.user_data[field] = user_input
        st.session_state.missing_fields.pop(0)

        # If more fields are missing, ask the next one
        if st.session_state.missing_fields:
            next_field = st.session_state.missing_fields[0]
            return f"I couldn't detect your {next_field}. Please enter it."
        else:
            # All missing fields filled
            st.session_state.step = "resume_extracted"
            return "Thanks! Type YES to save your resume or NO to cancel."

    # ---------------- Manual Resume Flow ----------------
    elif step == "ask_name":
        st.session_state.user_data["name"] = user_input
        st.session_state.step = "ask_email"
        return "What is your email?"

    elif step == "ask_email":
        st.session_state.user_data["email"] = user_input
        st.session_state.step = "ask_phone"
        return "What is your phone number?"

    elif step == "ask_phone":
        st.session_state.user_data["phone"] = user_input
        st.session_state.step = "ask_education"
        return "What is your highest degree?"

    elif step == "ask_education":
        st.session_state.user_data["education"] = user_input
        st.session_state.step = "ask_skills"
        return "List your skills separated by commas."

    elif step == "ask_skills":
        skills_list = [s.strip() for s in user_input.split(",") if s.strip()]
        st.session_state.user_data["skills"] = skills_list
        st.session_state.step = "ask_projects"
        return "Describe one key project."

    elif step == "ask_projects":
        st.session_state.user_data["projects"] = user_input
        st.session_state.step = "confirm"

        data = st.session_state.user_data
        return f"Confirm your details:\n\nName: {data['name']}\nEmail: {data['email']}\nPhone: {data['phone']}\nEducation: {data['education']}\nSkills: {', '.join(data['skills'])}\nProject: {data['projects']}\n\nType 'yes' to save or 'no' to cancel."

    elif step == "confirm":
        if user_input.lower() == "yes":
            data = st.session_state.user_data

            cursor.execute("INSERT OR IGNORE INTO users (name, email, phone) VALUES (?, ?, ?)",
                            (data["name"], data["email"], data["phone"]))
            user_id = cursor.lastrowid

            cursor.execute("INSERT INTO education (user_id, degree) VALUES (?, ?)",
                            (user_id, data["education"]))

            for skill in data["skills"]:
                cursor.execute("INSERT INTO skills (user_id, skill) VALUES (?, ?)",
                                (user_id, skill))

            cursor.execute("INSERT INTO projects (user_id, description) VALUES (?, ?)",
                            (user_id, data["projects"]))

            conn.commit()

            st.session_state.step = "menu"
            return "Resume saved successfully!"
        else:
            st.session_state.step = "menu"
            return "Cancelled."

    # ---------------- Edit Flow ----------------
    elif step == "load_email":
        user = get_user_by_email(user_input)
        if user:
            st.session_state.current_user_id = user[0]
            st.session_state.step = "edit_skills"
            skills = get_user_skills(user[0])
            return f"Welcome back {user[1]}! Your current skills: {', '.join(skills)}"
        else:
            return "No user found with that email."

    elif step == "edit_skills":
        user_id = st.session_state.current_user_id
        intent, skills = parse_skill_intent(user_input)

        if not skills:
            return "I couldn't detect any known skills in your message."

        responses = []
        for skill in skills:
            skill_cap = skill.capitalize()
            if intent == "add":
                if add_skill(user_id, skill_cap):
                    responses.append(f"{skill_cap} added.")
                else:
                    responses.append(f"{skill_cap} already exists.")
            elif intent == "remove":
                remove_skill(user_id, skill_cap)
                responses.append(f"{skill_cap} removed.")

        return "\n".join(responses)

# -----------------------------
# File uploader UI (SIDEBAR)
# -----------------------------
if st.session_state.step == "upload_resume":
    with st.sidebar:
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

        if uploaded_file is not None:
            text = extract_text_from_pdf(uploaded_file)
            
            st.sidebar.text_area("Extracted raw text", text, height=200)   #To be commented out if required for UX 
            
            text = normalize_pdf_text(text) 
            extracted = extract_resume_fields(text)

            st.session_state.user_data = extracted
            
            missing = []
            for key in ["name", "email", "phone"]:
                if not extracted.get(key):
                    missing.append(key)
            if missing:
                st.session_state.step = "ask_missing"
                st.session_state.missing_fields = missing
            else:
                st.session_state.step = "resume_extracted"   

            summary = (
                        f"I found the following details: \n\n"
                        f"Name: {extracted['name'] or 'Not detected'}\n"
                        f"Email: {extracted['email'] or 'Not detected'}\n"
                        f"Phone: {extracted['phone'] or 'Not detected'}\n"
                        f"Skills: {','.join(extracted['skills'] or 'Not detected')}\n"
                        f"Education: {','.join(extracted['education'] or 'Not detected')}\n"
                        f"Projects: {','.join(extracted['projects'] or 'Not detected')}\n"
                        )
                        
            if missing:
                summary += f"I could not detect your {missing[0]}. Please enter it"
            else:
                summary += "Type YES to save or NO to cancel."

            st.session_state.messages.append({
                "role":"assistant",
                "content": summary
            })
            st.rerun()
            st.stop()
# -----------------------------
# Chat input handling
# -----------------------------
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    reply = bot_reply(prompt)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)

# -----------------------------
# Initial message
# -----------------------------
if len(st.session_state.messages) == 0:
    welcome = "Hello! What would you like to do?\n1. Select 1 to create resume manually\n2. Select 2 to upload resume (auto extract)\n3. Select 3 to edit existing resume"
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.rerun()
