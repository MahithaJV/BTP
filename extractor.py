import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
# Bridge env var: langchain-google-genai expects GOOGLE_API_KEY
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pypdf. For image-based PDFs, you'd need OCR (pytesseract)."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        if text.strip():
            return text
        raise ValueError("No text extracted from PDF")
    except Exception as e:
        print(f"Warning: pypdf could not read {pdf_path}: {e}")
        # Fallback: try reading as plain text (handles mock/dummy files)
        try:
            with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if text.strip():
                print(f"Read {pdf_path} as plain text instead.")
                return text
        except Exception:
            pass
        return ""

def extract_structured_data(pdf_text):
    """
    Uses Gemini (via LangChain) to extract structured data from the FIR text.
    Returns a JSON string representing the structured record.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not found in environment. Using mock extraction.")
        return '{"fir_number": "MOCK-123", "date": "2023-10-01", "location": "Mumbai", "description": "Mock description of crime.", "complainant": "John Doe", "accused": "Unknown"}'
        
    print("Using Gemini to extract structured data from FIR text...")
    
    # Initialize the LLM
    # Note: Using "gemini-1.5-pro" as it's the widely available Pro model currently.
    # You can update this to "gemini-2.5-pro" when it becomes available in the API.
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    
    prompt = PromptTemplate.from_template(
        """You are an expert at parsing police First Information Reports (FIRs) in India.
        Extract the following information from the provided FIR text and return it strictly as a JSON object.
        Do not include any markdown formatting like ```json. Just the raw JSON.
        
        Fields to extract:
        - fir_number: The FIR number
        - date: Date of the incident
        - location: Location where the incident occurred
        - description: Brief description of the incident/crime
        - complainant: Name of the person filing the complaint
        - accused: Name(s) of the accused (if known)
        
        FIR Text:
        {text}
        """
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"text": pdf_text[:8000]}) # Limit text length to avoid token limits if necessary
        # Handle response.content being either a str or list of content parts
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        return content
    except Exception as e:
        print(f"Error during Gemini extraction: {e}")
        return "{}"

def process_pdfs(download_dir):
    """Processes all PDFs in the directory and returns a list of structured JSON records."""
    records = []
    
    if not os.path.exists(download_dir):
        print(f"Directory {download_dir} does not exist.")
        return records
        
    for filename in os.listdir(download_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(download_dir, filename)
            print(f"Processing {filename}...")
            
            text = extract_text_from_pdf(pdf_path)
            if text:
                structured_json = extract_structured_data(text)
                try:
                    record_dict = json.loads(structured_json)
                    records.append(record_dict)
                    print(f"Successfully extracted data for {record_dict.get('fir_number', 'Unknown')}")
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON from LLM response for {filename}")
                    print(f"Response was: {structured_json}")
    
    return records

if __name__ == "__main__":
    # Test with a dummy file if you have one
    process_pdfs("firs")
