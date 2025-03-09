import os
import streamlit as st
import requests
import spacy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to load SpaCy model safely
def load_spacy_model():
    model_name = "en_core_web_sm"
    try:
        return spacy.load(model_name)
    except OSError:
        st.error(f"SpaCy model '{model_name}' is missing. Ensure it's installed via `requirements.txt`.")
        st.stop()

# Load SpaCy model
nlp = load_spacy_model()

# API URLs
UPWORK_API_URL = "https://upwork-jobs-api2.p.rapidapi.com/active-freelance-7d"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Securely load API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Check if API keys are available
if not GROQ_API_KEY or not RAPIDAPI_KEY:
    st.error("API keys are missing. Please check your .env file.")
    st.stop()

# Function to fetch jobs from Upwork
def fetch_upwork_jobs(query, location):
    querystring = {"search": query, "location_filter": location}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "upwork-jobs-api2.p.rapidapi.com"
    }
    response = requests.get(UPWORK_API_URL, headers=headers, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching jobs: {response.text}")
        return []

# Function to generate a proposal using Groq API
def generate_proposal(job):
    prompt = f"""
    You are a professional Upwork proposal writer. Write a well-structured, engaging, and persuasive proposal for the following job:

    **Job Details:**
    - **Job Title**: {job.get('title', 'N/A')}
    - **Job Description**: {job.get('description_text', 'N/A')}
    - **Client Location**: {job.get('client_country', 'N/A')}
    - **Job URL**: {job.get('url', 'N/A')}

    **Proposal Structure:**
    - Start with a **polite greeting**.
    - Express **interest** and relevant **experience**.
    - Outline a **clear structured approach** to solving the problem.
    - Mention **relevant past projects** or skills.
    - Provide an **estimated timeline and budget** (if applicable).
    - Include a **direct job URL link** for reference.
    - End with a **friendly call to action**.

    **Instructions**:
    - DO NOT include <think>...</think> or any internal reasoning.
    - ONLY return the final **proposal text** in a **professional tone**.
    """

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }

    response = requests.post(GROQ_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Error: {response.json()}"

# Streamlit UI
st.title("Upwork Proposal Generator")

# Input fields for user
query = st.text_input("Enter Job Keyword (e.g., Data Engineer)", "Data Engineer")
location = st.text_input("Enter Location (optional)", "India")

if st.button("Fetch Jobs"):
    jobs = fetch_upwork_jobs(query, location)

    if not jobs:
        st.warning("No jobs found.")
    else:
        for job in jobs[:5]:  # Display top 5 jobs
            st.subheader(f"Job: {job['title']}")
            st.write(job.get("description_text", "No description available"))
            st.write(f"🔗 [Job Link]({job.get('url', '#')})")

            proposal_text = generate_proposal(job)
            st.text_area("Generated Proposal", proposal_text, height=200)
