# 🤖 AI Resume Chatbot with Automated Parsing and Profile Management

An intelligent resume assistant built using **Streamlit, spaCy, and SQLite** that allows users to upload resumes, automatically extract structured information, and manage their professional profile through a conversational chatbot interface.

This project simulates the core functionality of modern **Applicant Tracking Systems (ATS)** by combining Natural Language Processing (NLP), PDF parsing, and database management into an interactive web application.

---

## ✨ Key Features

### 📄 Resume Upload and Parsing

* Users can upload resumes in **PDF format**
* The system extracts:

  * Name
  * Email
  * Phone number
  * Skills
  * Education
  * Projects

### 🧠 NLP-Powered Information Extraction

* Uses **spaCy Named Entity Recognition (NER)** to detect candidate names
* Regex-based parsing for:

  * Email addresses
  * Phone numbers
* Dictionary + text scanning to detect technical skills

### 💬 Conversational Chatbot Interface

* Built using **Streamlit chat components**
* Users can:

  * Create resume profiles manually
  * Upload and auto-extract resumes
  * Edit existing profiles using natural language

Example:

```
User: I also know TensorFlow
Bot: TensorFlow added.
```

### 🗄️ Structured Database Storage

All extracted information is stored in a **SQLite relational database** with normalized schema:

* `users` → basic profile
* `education` → multiple degrees
* `skills` → multiple skills
* `projects` → project descriptions

### ✍️ Intelligent Missing Data Handling

If any field is not detected during parsing, the chatbot automatically asks the user to provide the missing information before saving.

---

## 🧱 Tech Stack

| Component   | Technology |
| ----------- | ---------- |
| Frontend UI | Streamlit  |
| NLP Engine  | spaCy      |
| PDF Parsing | PyPDF2     |
| Database    | SQLite     |
| Language    | Python     |

---

## 🏗️ System Architecture

```
PDF Resume
    │
    ▼
Text Extraction (PyPDF2)
    │
    ▼
Text Normalization + Cleaning
    │
    ▼
NLP & Regex Parsing
    │
    ▼
Structured Data
    │
    ▼
SQLite Database
    │
    ▼
Chatbot Editing Interface
```

---

## 📂 Project Structure

```
├── app.py                # Main Streamlit application
├── resume.db             # SQLite database (auto-generated)
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## 🔍 Information Extraction Logic

### Name Detection

Uses spaCy NER:

```python
if ent.label_ == "PERSON":
```

### Skill Detection

Uses a hybrid approach:

* Known skill dictionary
* Case-insensitive text matching

### Project Section Detection

The parser identifies project sections and extracts all lines until the next resume section appears.

---

## 💬 Chatbot Workflow

1. User chooses:

   ```
   1. Create manually
   2. Upload resume
   3. Edit existing
   ```

2. Resume is parsed or manually entered

3. User confirms extracted data

4. Data is stored in SQLite

5. User can later edit skills using natural language

---

## 📸 Screenshots (Suggested)

You can add:

* Chat interface
* Resume upload panel
* Extracted data summary

---

## 🚀 How to Run the Project

### 1. Clone the repository

```
git clone https://github.com/yourusername/ai-resume-chatbot.git
cd ai-resume-chatbot
```

### 2. Install dependencies

```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run the Streamlit app

```
streamlit run app.py
```

---

## 🧪 Example Use Cases

* Students uploading resumes to build structured profiles
* Demonstrating NLP-based information extraction
* Learning how chatbots integrate with databases
* Simulating a simplified ATS pipeline

---

## 🧠 Concepts Demonstrated

This project showcases practical implementation of:

* Natural Language Processing (NER, token parsing)
* Resume parsing and section detection
* Conversational state management using session state
* Relational database design
* End-to-end AI application development

---

## 🔮 Future Improvements

* Semantic skill extraction using embedding similarity
* Support for DOCX resumes
* Admin dashboard to search candidates
* Export structured profile back to formatted resume

---

## 👨‍💻 Author

**Your Name**
Final Year Project — Artificial Intelligence & Machine Learning

---

## 📜 License

This project is licensed under the MIT License.

