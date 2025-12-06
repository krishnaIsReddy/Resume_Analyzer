"""
AI Resume Analyzer - Main Application File

This Streamlit application uses Google's Gemini AI to analyze and improve resumes.
It provides two main functionalities:
1. Resume Analysis: Provides feedback and suggestions for improvement
2. Resume Recreation: Automatically rewrites and reformats resumes into professional PDFs

Design Decisions:
- Using Streamlit for rapid web app development without frontend code
- Google Gemini AI for natural language processing and resume analysis
- PDF parsing with PyPDF2 for extracting text from uploaded resumes
- Jinja2 templates for structured HTML resume generation
- pdfkit for converting HTML templates to PDF files
"""

import streamlit as st
#from openai import OpenAI
import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
# PyPDF2 import PdfFileReader
import PyPDF2
import io
from fpdf import FPDF
import traceback
import unicodedata
import json
import re
from jinja2 import Environment, FileSystemLoader
#from weasyprint import HTML
#import tempfile
import pdfkit

# Load environment variables from .env file
# This keeps API keys secure and out of version control
load_dotenv()
#api_key = st.secrets["GEMINI_AI_API"]  # Alternative: use Streamlit secrets for deployment

# Streamlit UI Configuration
# Using "centered" layout for a clean, professional appearance
st.set_page_config(page_title="AI Resume Fixer", layout="centered")
st.title("AI Resume Analyzer")
st.markdown("Upload your resume below to get AI suggestions:")

#OPENAI_API_KEY = os.getenv(_______)

# User Interface Elements
# File uploader accepts both PDF and text files for flexibility
upload = st.file_uploader("Upload your resume (PDF/txt)", type=["pdf", "txt"])
# Optional job description input to tailor AI suggestions to specific roles
job_role = st.text_input("Enter the job role description")
# Two main action buttons for different use cases
analyze = st.button("Analyze Resume")  # Get feedback and suggestions
recreate = st.button("Create New Resume")  # Generate improved resume PDF


def parse_pdf(pdf_name):
    """
    Extracts text content from a PDF file.
    
    Design Decision: Using PyPDF2 instead of older PdfFileReader for better compatibility
    with modern PDF formats and improved text extraction accuracy.
    
    Args:
        pdf_name: File-like object (BytesIO) containing PDF data
        
    Returns:
        str: Extracted text from all pages, with newlines between pages
    """
    #pdfFileObject = open(pdf_name, 'rb')
    #pdfReader = PdfFileReader(pdfFileObject)
    pdf_reader = PyPDF2.PdfReader(pdf_name)

    resume_text = ''
    # Iterate through all pages to extract complete resume content
    for page in pdf_reader.pages:
        #pageObj = pdfReader.getPage(i)
        resume_text += page.extract_text() + "\n"
    return resume_text


def parse_file(upload):
    """
    Universal file parser that handles both PDF and text file uploads.
    
    Design Decision: Single function to handle multiple file types, making the code
    more maintainable and the UI simpler (one uploader for all formats).
    
    Args:
        upload: Streamlit UploadedFile object
        
    Returns:
        str: Text content of the uploaded file
    """
    # Check file type and route to appropriate parser
    if upload.type == "application/pdf":
        # Convert uploaded file to BytesIO for PyPDF2 compatibility
        # This avoids writing to disk and keeps everything in memory
        return parse_pdf(io.BytesIO(upload.read()))
    # For text files, decode UTF-8 to handle international characters
    return upload.read().decode("utf-8")



def generate(resume_file):
    """
    Generates an improved resume in JSON format using Google Gemini AI.
    
    This function is used for the "Create New Resume" feature. It sends the original
    resume and job description to Gemini AI with specific instructions to:
    1. Rewrite the resume professionally
    2. Format it as structured JSON
    3. Align it with the job description if provided
    
    Design Decisions:
    - Using streaming API for better user experience (shows progress)
    - JSON output format for structured data that can be easily templated
    - System instructions to ensure consistent output format
    - Safety settings to prevent inappropriate content generation
    - Thinking config to allow the model to reason through the task
    
    Args:
        resume_file: String containing the text content of the original resume
        
    Returns:
        str: JSON-formatted string containing the improved resume data
    """

    #resume_file = parse_file(upload)

    # Construct the prompt with clear instructions for the AI
    # Design: Using triple-quoted strings to include both resume and job description
    # This allows the AI to tailor the resume to specific job requirements
    prompt = f"""Here is a resume that needs to be rewritten professionally. 
    Do not provide feedback, your job is to rewrite the resume in the 'Jake's resume' format. Rewrite the resume to improve clarity, professionalism, and alignment with general job standards.
    Please format your output as a JSON object with the following key names: name, contact, education (list of entries), 
    experience (list of entries), skills (list of skills), projects (list of entries), awards (list of entries). 
    If you need to, make other key names if prominent in the resume, make sure to make it a list of entries as well. 
    Do not output text outside of the JSON. Do not have the word 'JSON' in any form in the JSON formatting. do not have '''json '''.
    Make sure the resume is within one page.
    at all.

            Resume:
            \"\"\"{resume_file}\"\"\"

            Job Description:
            \"\"\"{job_role}\"\"\"

    """
    client = genai.Client(
        #api_key=st.secrets["GEMINI_AI_API"]
        api_key = os.getenv("GEMINI_AI_API"),
    )

    model = "models/gemini-2.5-flash"
    # Structure the API request content
    # Design: Using Content and Part types for type safety and API compatibility
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    # Configure the AI generation parameters
    # Design Decisions:
    # - max_output_tokens=4096: Sufficient for a one-page resume in JSON format
    # - thinking_config: Allows model to reason through the resume improvement task
    # - Safety settings: Strict blocking to ensure professional, appropriate content
    # - response_mime_type="text/plain": We'll parse JSON from plain text response
    # - system_instruction: Reinforces the JSON-only output requirement
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=4096,  # Enough tokens for comprehensive resume data
        thinking_config = types.ThinkingConfig(
            thinking_budget=2000,  # Allows model to think through improvements
        ),
        safety_settings=[
            # Strict safety settings ensure professional, appropriate content
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
        ],
        response_mime_type="text/plain",  # We'll extract JSON from plain text
        system_instruction=[
            # System instruction reinforces the output format requirement
            # This helps ensure consistent JSON structure even if prompt is ambiguous
            types.Part.from_text(text="""You are an expert resume reviewer. 
                                 Your only task is to generate structured data for an improved resume, 
                                 based on the provided resume and job description. Do not output any 
                                 explanations or formatted text. Only output a valid JSON object with the following keys:
                                 name (string), contact (string), education (list of entries), experience (list of entries), 
                                 skills (list of strings), projects (list of entries), awards (list of entries), activities (list of entries).
                                 Each entry in lists should itself be a JSON object with appropriate fields (title, description, date, etc. where applicable). 
                                 Your output must be a single JSON object and nothing else.

"""),
        ],
    )

    # Use streaming API for better user experience
    # Design: Streaming allows users to see progress, though we accumulate the full response
    # Alternative: Non-streaming API would be simpler but less responsive
    full_response = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        full_response += chunk.text

    return full_response




def transform_pdf(resume_data):
    """
    Converts structured resume data (dict) into a PDF file using HTML templating.
    
    Design Decisions:
    - Using Jinja2 templates for flexible, maintainable HTML generation
    - pdfkit with wkhtmltopdf for reliable HTML-to-PDF conversion
    - Template-based approach allows easy styling changes without code changes
    - Returns bytes directly for Streamlit download button compatibility
    
    Alternative considered: WeasyPrint (commented out) - more Python-native but
    less reliable for complex layouts. pdfkit provides better rendering quality.
    
    Args:
        resume_data: Dictionary containing structured resume data (name, contact, etc.)
        
    Returns:
        bytes: PDF file as bytes, ready for download
    """
    # Load Jinja2 template from template directory
    # Design: Separating templates from code makes styling changes easier
    env = Environment(loader=FileSystemLoader("template"))
    template = env.get_template("resume_template.html")
    # Render template with resume data
    # Using **resume_data unpacks the dictionary as keyword arguments
    html_out = template.render(**resume_data)

    # Configure pdfkit to use wkhtmltopdf executable
    # Design: Hardcoded Windows path - could be made configurable for cross-platform
    # False parameter means don't save to file, return bytes instead
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    pdf_bytes = pdfkit.from_string(html_out, False, configuration=config)
    return pdf_bytes
    #pdf_io = io.BytesIO()
    #HTML(string = html_out).write_pdf(pdf_io)
    #pdf_io.seek(0)

    #return pdf_io.read()




def clean_text(text):
    """
    Normalizes Unicode text to Latin-1 encoding for PDF compatibility.
    
    Design Decision: FPDF library has limited Unicode support, so we normalize
    and convert to Latin-1 to avoid encoding errors. This function is used
    as a fallback for the alternative PDF generation method.
    
    Args:
        text: Unicode string that may contain special characters
        
    Returns:
        str: Text normalized to Latin-1 encoding
    """
    # NFKD normalization decomposes characters, then encode/decode to Latin-1
    # This removes characters that can't be represented in Latin-1
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")



def create_pdf(full_response):
    """
    Alternative PDF generation method using FPDF (currently not used).
    
    This function was an alternative approach to PDF generation but was replaced
    by the template-based transform_pdf() method for better formatting control.
    Kept for reference or as a fallback option.
    
    Design: FPDF provides programmatic PDF creation but lacks the flexibility
    of HTML/CSS templating for complex layouts.
    
    Args:
        full_response: Text content to convert to PDF
        
    Returns:
        io.BytesIO: PDF file as a BytesIO buffer
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Times", size=12)

    #lines = full_response.split('\n')
    # Clean text to handle Unicode characters before adding to PDF
    lines = clean_text(full_response).split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, txt = line)
    
    # Convert PDF to bytes for download
    buffer = io.BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_output)
    #pdf.output(buffer)
    buffer.seek(0)
    return buffer



def clean_json(text):
    """
    Cleans AI-generated text to extract valid JSON.
    
    AI models sometimes wrap JSON in markdown code blocks (```json ... ```)
    or add extra text. This function removes those artifacts to get clean JSON.
    
    Design Decision: Robust parsing handles various AI output formats, making
    the system more reliable even if the AI doesn't follow instructions exactly.
    
    Args:
        text: Raw text from AI that may contain markdown formatting or extra text
        
    Returns:
        str: Clean JSON string ready for parsing
    """
    # Remove leading markdown code block markers (```json, ```, etc.)
    text = re.sub(r"^```.*?\n", "", text)
    # Remove trailing markdown code block markers
    text = re.sub(r"\n```$", "", text)
    text = text.strip()

    # Find the last closing brace to handle cases where AI adds extra text
    # This ensures we only parse the complete JSON object
    last_brace = text.rfind('}')
    if last_brace != -1:
        text = text[:last_brace + 1]
    return text


if recreate and upload:
    try:
        # Step 1: Parse the uploaded file to extract text content
        resume_file = parse_file(upload)
        
        # Step 2: Generate improved resume using AI (returns JSON string)
        new_resume = generate(resume_file)

        # Step 3: Clean the AI response to extract valid JSON
        json_text = new_resume
        json_text = clean_json(json_text)  # Remove markdown formatting, extra text
        
        # Step 4: Parse JSON string into Python dictionary
        # This allows us to pass structured data to the template
        resume_data = json.loads(json_text)
        
        # Step 5: Convert structured data to PDF using HTML template
        pdf_bytes = transform_pdf(resume_data)
        #except json.JSONDecodeError as e:
            #st.error(f"Error {str(e)}")
            #st.text(json_text)
            #resume_data = {}


        #st.subheader("Parsed Resume Data:")
        #st.json(resume_data)

        #new_pdf = create_pdf(json_text)  # Alternative PDF generation method
        # Step 6: Provide download button for the generated PDF
        # Design: Streamlit's download_button handles file download in browser
        st.download_button(label="Download Revised Resume (PDF)", 
                           #data = new_pdf,
                           data = pdf_bytes,
                           file_name ="updated_resume.pdf",
                           mime = "application/pdf")

    except Exception as e:
        # Error handling: Show user-friendly error and full traceback for debugging
        st.error(f"File does not exist: {str(e)}")
        st.text(traceback.format_exc())




def generate_idea(resume_file):
    """
    Generates feedback and suggestions for resume improvement using Google Gemini AI.
    
    This function is used for the "Analyze Resume" feature. Unlike generate(),
    this function provides human-readable feedback and suggestions rather than
    structured JSON. It focuses on:
    1. Providing actionable feedback
    2. Suggesting STAR format improvements
    3. Comparing old vs. new resume lines
    4. General tips for matching job descriptions
    
    Design Decisions:
    - Lower token limit (2000) since we're generating feedback, not full resume
    - Different system instruction focused on analysis rather than generation
    - Plain text output for easy display in Streamlit markdown
    
    Args:
        resume_file: String containing the text content of the resume
        
    Returns:
        str: Formatted text containing feedback and suggestions
    """

    # Construct prompt for analysis and feedback
    # Design: Different prompt structure than generate() - focuses on feedback
    # STAR format (Situation, Task, Action, Result) is industry standard for resume bullets
    prompt = f"""Here is a resume that needs to be rewritten professionally. 
    Provide feedback and then rewrite the resume to improve clarity, professionalism, 
    and alignment with general job standards. Make sure to point out tips for using the STAR format
    for the experiences section of the resume. 

            Resume:
            \"\"\"{resume_file}\"\"\"

            Job Description:
            \"\"\"{job_role}\"\"\"
    """

    # Initialize Gemini AI client (same as generate() function)
    client = genai.Client(
        #api_key=st.secrets["GEMINI_AI_API"]
        api_key = os.getenv("GEMINI_AI_API"),
    )

    model = "models/gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    # Configuration for feedback generation
    # Design: Lower token limits since feedback is typically shorter than full resume
    # Lower thinking budget as analysis is less complex than full resume generation
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=2000,  # Sufficient for feedback, lower than full resume generation
        thinking_config = types.ThinkingConfig(
            thinking_budget=1000,  # Less thinking needed for analysis vs. generation
        ),
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_LOW_AND_ABOVE",  # Block most
            ),
        ],
        response_mime_type="text/plain",
        system_instruction=[
            # System instruction for feedback mode
            # Design: Focuses on providing actionable feedback with examples
            # Note: There's a typo in the original ("change them based on an job")
            # but keeping it as-is to maintain original behavior
            types.Part.from_text(text="""You are an expert resume reviewer with years of experience in job recruitment. 
                                 It is your task to analyze resumes that are given to you change them based on an job 
                                 description provided to make it the most effective for that job application. Do not 
                                  up any experiences, only rewrite the experiences given so that they sound professional 
                                 and sound appropriate for the job listing. If no job listing is provided, then make the 
                                 resume sound as professional as possible. Your job is to provide bullet points. Within a 
                                 few of the bullet points, you need to provide the old line of text from the resume and the new, 
                                 revised line of text next to it. A few of the other bullet points will have general tips on what 
                                 needs to be fixed with the resume to help match the job description. 
"""),
        ],
    )

    # Accumulate streaming response for feedback display
    resume_tips = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        resume_tips += chunk.text
    return resume_tips




# Main Application Logic - Resume Analysis Flow
# This block executes when user clicks "Analyze Resume" button and has uploaded a file
if analyze and upload:
    try: 
        # Step 1: Parse the uploaded file to extract text content
        resume_file = parse_file(upload)
        
        # Step 2: Generate feedback and suggestions using AI
        new_idea = generate_idea(resume_file)
        
        # Step 3: Display the feedback to the user
        # Design: Using markdown for rich text formatting of AI feedback
        st.markdown("Here are some tips for your resume:")
        st.markdown(new_idea)  # Markdown allows formatting in AI response

    except Exception as e:
        # Error handling: Show user-friendly error and full traceback for debugging
        st.error(f"We ran into an error: {str(e)}")
        st.text(traceback.format_exc())




