# AI Resume Analyzer

A Streamlit-based web application that uses Google's Gemini AI to analyze and improve resumes. The application provides AI-powered suggestions for resume enhancement and can automatically reformat resumes into a professional "Jake's Resume" style format, generating a downloadable PDF.

## 📋 Project Overview and Purpose

The **AI Resume Analyzer** is designed to help job seekers improve their resumes through AI-powered analysis and suggestions. The application offers two main features:

1. **Resume Analysis**: Upload your resume and receive detailed feedback and suggestions for improvement, including tips on using the STAR (Situation, Task, Action, Result) format for experience descriptions.

2. **Resume Recreation**: Automatically rewrite and reformat your resume to match professional standards and align with a specific job description. The improved resume is generated as a downloadable PDF.

The application uses Google's Gemini 2.5 Flash AI model to analyze resume content, provide professional feedback, and generate structured resume data that is then converted into a professionally formatted PDF using HTML templates.

## 🎥 Video Demonstration

## 🚀 Installation and Setup Instructions

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- wkhtmltopdf (for PDF generation)
  - Windows: Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
  - Install to default location: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd resume_AI_analyzer
```

### Step 2: Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or using `pip`:

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

1. Create a `.env` file in the project root directory:

```bash
touch .env
```

2. Add your Google Gemini API key to the `.env` file:

```
GEMINI_AI_API=your_api_key_here
```

**Note**: The `.env` file is already included in `.gitignore` to protect your API key.

### Step 4: Verify Template Files

Ensure the resume template exists:

- `template/resume_template.html` - HTML template for resume formatting

## 💻 How to Run the Program

### Running with uv (Recommended)

```bash
uv run streamlit run main.py
```

### Running with Python Module

```bash
uv run python -m streamlit run main.py
```

### Running with Global Streamlit Installation

If Streamlit is installed globally:

```bash
streamlit run main.py
```

### Running on a Custom Port

```bash
uv run streamlit run main.py --server.port 8502
```

### Accessing the Application

Once the application starts, you should see output similar to:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open the provided URL in your web browser to access the application.

## 📖 How to Use the Application

1. **Upload Your Resume**: Click "Upload your resume (PDF/txt)" and select your resume file (PDF or text format).

2. **Enter Job Description** (Optional): Enter the job role description to tailor the resume analysis and improvements.

3. **Analyze Resume**: Click the "Analyze Resume" button to receive AI-powered feedback and suggestions for improvement.

4. **Create New Resume**: Click the "Create New Resume" button to automatically rewrite and reformat your resume. The improved resume will be available as a downloadable PDF.

## 🔧 Technologies and Libraries Used

### Core Technologies

- **Python 3.12+**: Programming language
- **Streamlit**: Web application framework for creating the user interface
- **Google Gemini AI**: AI model for resume analysis and generation (using `google-genai` package)

### Key Libraries

- `streamlit>=1.45.1`: Web app framework
- `google-genai>=1.18.0`: Google Gemini AI client library
- `python-dotenv>=1.1.0`: Environment variable management
- `PyPDF2>=3.0.1`: PDF parsing and text extraction
- `pdfkit>=1.0.0`: HTML to PDF conversion
- `jinja2`: Template engine for HTML resume generation
- `fpdf>=1.7.2`: PDF generation library (alternative method)
- `json`: JSON parsing for structured resume data

### Additional Tools

- **wkhtmltopdf**: Command-line tool for converting HTML to PDF
- **uv**: Modern Python package manager (alternative to pip)

## 👤 Author(s) and Contribution Summary

### Author

Krishnateja Reddy (krishnateja)

### Contribution Summary

This project was developed as a solution to help job seekers improve their resumes using AI technology. Key contributions include:

- **AI Integration**: Integrated Google Gemini AI for intelligent resume analysis and generation
- **PDF Processing**: Implemented PDF parsing and generation capabilities
- **Template System**: Created HTML template-based resume formatting system
- **User Interface**: Built an intuitive Streamlit web interface for easy interaction
- **Error Handling**: Implemented robust error handling and user feedback mechanisms
