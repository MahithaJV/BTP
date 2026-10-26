import os
import sys
import re
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pypdf import PdfReader
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
        # Fallback: try reading as plain text (handles mock/text-based files)
        try:
            with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if text.strip():
                return text
        except Exception:
            pass
        return ""

def _regex_extract_fallback(text):
    """Regex-based fallback extraction if Gemini API is temporarily busy/overloaded."""
    data = {}
    fir_m = re.search(r'FIR No:\s*([^\n,]+)', text)
    data["fir_number"] = fir_m.group(1).strip() if fir_m else "Unknown"
    
    date_m = re.search(r'Date:\s*([^\n,]+)', text)
    data["date"] = date_m.group(1).strip() if date_m else "Unknown"
    
    loc_m = re.search(r'Place of Occurrence:\s*([^\n]+)', text)
    data["location"] = loc_m.group(1).strip() if loc_m else "Maharashtra"
    
    comp_m = re.search(r'Complainant[^:]*:\s*\n?\s*Name:\s*([^\n]+)', text)
    data["complainant"] = comp_m.group(1).strip() if comp_m else "Anonymous"
    
    acc_m = re.search(r'Accused Name:\s*([^\n,]+)', text)
    data["accused"] = acc_m.group(1).strip() if acc_m else "Unknown"
    
    desc_m = re.search(r'Brief Description of Incident:\s*\n?\s*([^\n]+(?:\n[^\n]+)*)', text)
    data["description"] = desc_m.group(1).strip() if desc_m else "Incident reported under Cr.P.C."
    
    return json.dumps(data)

def extract_structured_data(pdf_text):
    """
    Uses Gemini (via LangChain) to extract structured data from the FIR text.
    Returns a JSON string representing the structured record.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return _regex_extract_fallback(pdf_text)
        
    print("  Using Gemini LLM to extract structured data...", flush=True)
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=0,
            timeout=25,
            max_retries=1
        )
        
        prompt = PromptTemplate.from_template(
            """You are an expert at parsing police First Information Reports (FIRs) in India.
            Extract the following information from the provided FIR text and return it strictly as a JSON object.
            Do not include any markdown formatting like ```json. Just the raw JSON.
            
            Fields to extract:
            - fir_number: The FIR number (e.g. 0468, 2287, etc.)
            - date: Date of registration or occurrence (format: DD/MM/YYYY). Prefer registration date if available.
            - location: Location/place of occurrence where the incident occurred
            - description: Brief factual description of the incident/crime
            - complainant: Name of the person filing the complaint
            - accused: Name(s) of the accused (if known)
            
            FIR Text:
            {text}
            """
        )
        
        chain = prompt | llm
        response = chain.invoke({"text": pdf_text[:8000]})
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        content = str(content).strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
    except Exception as e:
        print(f"  Gemini extraction notice ({e}), applying intelligent parser fallback...", flush=True)
        return _regex_extract_fallback(pdf_text)

def process_pdfs(download_dir, target_files=None):
    """
    Processes PDFs in the directory and returns a list of structured JSON records.
    Skips files whose FIR numbers are already saved with coordinates in Supabase
    to conserve Gemini API quota and accelerate execution.
    """
    records = []

    if not os.path.exists(download_dir):
        print(f"Directory {download_dir} does not exist.", flush=True)
        return records

    # Query already stored FIR numbers with valid coordinates
    existing_firs = set()
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            resp = supabase.table("fir_records").select("fir_number, coordinates").execute()
            for r in (resp.data or []):
                if r.get("fir_number") and r.get("coordinates"):
                    existing_firs.add(str(r["fir_number"]).strip())
    except Exception as e:
        print(f"  Notice checking existing FIRs: {e}", flush=True)

    if target_files:
        files_to_process = [os.path.basename(f) for f in target_files]
    else:
        files_to_process = sorted(os.listdir(download_dir))

    pdf_files = [f for f in files_to_process if f.lower().endswith(".pdf")]
    print(f"Checking {len(pdf_files)} PDF file(s) in {download_dir}...", flush=True)

    for filename in pdf_files:
        pdf_path = os.path.join(download_dir, filename)

        # Quick check if FIR number prefix (e.g. '0630' from '0630 Publish FIR.pdf') is already stored
        file_prefix = filename.split()[0].strip() if " " in filename else ""
        if file_prefix and file_prefix in existing_firs:
            print(f"  [Skipping Cached PDF] FIR #{file_prefix} is already stored with heat coordinates.", flush=True)
            continue

        print(f"Processing new PDF: {filename}...", flush=True)
        text = extract_text_from_pdf(pdf_path)
        if text:
            structured_json = extract_structured_data(text)
            try:
                record_dict = json.loads(structured_json)
                records.append(record_dict)
                print(f"  [OK] Extracted data for FIR #{record_dict.get('fir_number', 'Unknown')}", flush=True)
            except json.JSONDecodeError:
                print(f"  [Fail] Could not parse JSON for {filename}", flush=True)

    return records
