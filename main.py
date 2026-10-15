import os
from scraper import scrape_firs
from extractor import process_pdfs
from agent import process_agentic_layer
from database import save_to_database

def main():
    print("=== FIR Processing Pipeline Started ===")
    
    # 1. Selenium Scraping -> FIR PDFs Downloaded
    print("\n--- Step 1: Scraping FIRs ---")
    download_dir = "firs_downloaded"
    try:
        download_dir = scrape_firs("firs_downloaded")
    except Exception as e:
        print(f"[Warning] Scraper failed ({e}). Continuing with mock data...")
    
    # If no PDFs were actually downloaded (because it's a mock), let's create a dummy one just for testing the rest of the flow
    # This is just for demonstration purposes so you can check if it's working without actual PDFs.
    if not os.path.exists(download_dir) or len(os.listdir(download_dir)) == 0:
        print("[Demo] Creating a mock PDF file to test the pipeline...")
        os.makedirs(download_dir, exist_ok=True)
        # Note: A real PDF would be created here. We just leave it empty so the extractor handles it or mocks it.
        # But let's let the extractor handle the fact that there might not be a real PDF if we don't have one.
        # Actually, let's create a dummy txt file renamed to pdf just so the file list picks it up.
        sample_fir_text = """
FIRST INFORMATION REPORT (Under Section 154 Cr.P.C.)
1. District: Mumbai City, Police Station: Dadar Police Station
   FIR No: 0248/2026, Date & Time of FIR: 14/10/2026 18:45 hrs
2. Act & Sections: Section 379 IPC (Theft)
3. Occurrence of Offence:
   Date: 14/10/2026, Time: 15:30 hrs
   Place of Occurrence: Platform No. 1, Dadar Railway Station, Mumbai
4. Complainant / Informant:
   Name: Rajesh Kumar Sharma
   Address: Flat 402, Sunrise Apts, Dadar West, Mumbai
5. Details of Known / Suspected / Unknown Accused with full particulars:
   Accused Name: Unknown male, approx 25-30 years old, wearing dark jacket
6. Brief Description of Incident:
   Complainant was boarding the local train at Dadar platform 1 when an unknown person snatched his leather bag containing a Dell laptop and wallet with Rs. 5000 cash and fled towards the foot overbridge.
"""
        with open(os.path.join(download_dir, "dummy_fir.pdf"), "w", encoding="utf-8") as f:
            f.write(sample_fir_text.strip())
    
    # 2. Gemini 2.5 Pro (OCR + Extraction via LangChain) -> Structured FIR Record JSON
    print("\n--- Step 2: Extraction & OCR ---")
    structured_records = process_pdfs(download_dir)
    
    if not structured_records:
        print("No records extracted. Exiting.")
        return
        
    print(f"Extracted {len(structured_records)} records.")
    
    # 3. Agentic Layer (LLM Crime Classification + Geocoding)
    print("\n--- Step 3: Agentic Layer ---")
    enhanced_records = process_agentic_layer(structured_records)
    
    # 4. Supabase PostgreSQL Database
    print("\n--- Step 4: Database Storage ---")
    save_to_database(enhanced_records)
    
    print("\n=== FIR Processing Pipeline Completed ===")
    print("To test it for real:")
    print("1. Set up your API keys in the .env file")
    print("2. Implement the exact Selenium selectors in scraper.py")
    print("3. Ensure your Supabase table schema matches the JSON structure")

if __name__ == "__main__":
    main()
