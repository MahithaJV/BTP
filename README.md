Pipeline Orchestrator (

main.py
)

Coordinates the entire workflow from scraping to database insertion via 

main()
.
Generates a sample mock FIR document (

dummy_fir.pdf
) automatically if no live PDFs are found, allowing end-to-end testing without running the scraper.
Web Scraper (

scraper.py
)

Implements 

scrape_firs()
 using Selenium WebDriver (Chrome).
Configures headless download settings to capture published FIR PDFs from portals (such as the Maharashtra Police portal).
Document Ingestion & LLM Extraction (

extractor.py
)



extract_text_from_pdf()
: Reads FIR PDFs using pypdf with plain-text fallback.


extract_structured_data()
: Prompts Google Gemini (gemini-3.1-flash-lite via LangChain) to parse unstructured police FIR text into structured JSON fields:
fir_number, date, location, description, complainant, accused.


process_pdfs()
: Batch processes all downloaded PDFs in a directory.
Agentic Layer & Intelligence (

agent.py
)



classify_crime()
: Uses Gemini to perform multi-label classification on the FIR incident description (e.g., Theft, Property Crime, Assault, Cybercrime).


geocode_location()
: Queries the Google Maps Geocoding API to resolve the text location into latitude and longitude (lat, lng).


process_agentic_layer()
: Enriches records with the generated crime tags and coordinates.
Database Storage & Inspection (

database.py
 & 

view_records.py
)



save_to_database()
: Saves the enriched FIR records into a Supabase PostgreSQL table (fir_records). Includes mock fallbacks if credentials are not configured.


view_records()
: Quick CLI utility to query and inspect stored records from Supabase.
Configuration & Dependencies



.env.example
: Template for GEMINI_API_KEY, GOOGLE_MAPS_API_KEY, SUPABASE_URL, and SUPABASE_KEY.


requirements.txt
: Lists required packages (selenium, langchain, langchain-google-genai, supabase, pypdf, etc.).
