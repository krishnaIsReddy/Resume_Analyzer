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

load_dotenv()

st.set_page_config(page_title="AI Resume Fixer", layout="centered")
st.title("AI Resume Fixer")
st.markdown("Upload your resume below to get AI suggestions:")

#OPENAI_API_KEY = os.getenv(_______)

upload = st.file_uploader("Upload your resume (PDF/txt)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role description")
analyze = st.button("Analyze Resume")
recreate = st.button("Create New Resume")


#parse the resume pdf
def parse_pdf(pdf_name):
    #pdfFileObject = open(pdf_name, 'rb')
    #pdfReader = PdfFileReader(pdfFileObject)
    pdf_reader = PyPDF2.PdfReader(pdf_name)

    resume_text = ''
    for page in pdf_reader.pages:
        #pageObj = pdfReader.getPage(i)
        resume_text += page.extract_text() + "\n"
    return resume_text


def parse_file(upload):
    if upload.type == "application/pdf":
        return parse_pdf(io.BytesIO(upload.read()))
    return upload.read().decode("utf-8")



#Check if the file is empty or not
#------


#Use gemini ai api


def generate(resume_file):

    #resume_file = parse_file(upload)

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
        api_key=os.getenv("GEMINI_AI_API"),
    )

    model = "gemini-2.5-flash-preview-04-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=4096,
        thinking_config = types.ThinkingConfig(
            thinking_budget=2000,
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

    full_response = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        full_response += chunk.text

    return full_response




def transform_pdf(resume_data):
    env = Environment(loader=FileSystemLoader("template"))
    template = env.get_template("resume_template.html")
    html_out = template.render(**resume_data)

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    pdf_bytes = pdfkit.from_string(html_out, False, configuration=config)
    
    return pdf_bytes




def clean_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")



def create_pdf(full_response):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Times", size=12)

    #lines = full_response.split('\n')
    lines = clean_text(full_response).split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, txt = line)
    
    buffer = io.BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_output)
    #pdf.output(buffer)
    buffer.seek(0)
    return buffer



def clean_json(text):
            # Remove leading ```json or ``` or ```text
            text = re.sub(r"^```.*?\n", "", text)
            # Remove trailing ```
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

            last_brace = text.rfind('}')
            if last_brace != -1:
                text = text[:last_brace + 1]
            return text


if recreate and upload:
    try:
        resume_file = parse_file(upload)
        new_resume = generate(resume_file)

        json_text = new_resume
        json_text = clean_json(json_text)
        

        resume_data = json.loads(json_text)
        pdf_bytes = transform_pdf(resume_data)
        #except json.JSONDecodeError as e:
            #st.error(f"Error {str(e)}")
            #st.text(json_text)
            #resume_data = {}


        #st.subheader("Parsed Resume Data:")
        #st.json(resume_data)

        #new_pdf = create_pdf(json_text)
        st.download_button(label="Download Revised Resume (PDF)", 
                           #data = new_pdf,
                           data = pdf_bytes,
                           file_name ="updated_resume.pdf",
                           mime = "application/pdf")

    except Exception as e:
        st.error(f"File does not exist: {str(e)}")
        st.text(traceback.format_exc())




#Building first button operation

    
def generate_idea(resume_file):

    prompt = f"""Here is a resume that needs to be rewritten professionally. 
    Provide feedback and then rewrite the resume to improve clarity, professionalism, 
    and alignment with general job standards. Make sure to point out tips for using the STAR format
    for the experiences section of the resume. 

            Resume:
            \"\"\"{resume_file}\"\"\"

            Job Description:
            \"\"\"{job_role}\"\"\"
    """

    client = genai.Client(
        api_key=os.getenv("GEMINI_AI_API"),
    )

    model = "gemini-2.5-flash-preview-04-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=2000,
        thinking_config = types.ThinkingConfig(
            thinking_budget=1000,
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

    resume_tips = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        resume_tips += chunk.text
    return resume_tips




if analyze and upload:
    try: 
        resume_file = parse_file(upload)
        new_idea = generate_idea(resume_file)
        st.markdown("Here are some tips for your resume:")
        st.markdown(new_idea)

    except Exception as e:
        st.error(f"We ran into an error: {str(e)}")
        st.text(traceback.format_exc())




