import os
import sys
import time
import datetime
from scraper import scrape_firs, TARGET_CITIES
from extractor import process_pdfs
from agent import process_agentic_layer
from database import save_to_database

# Configure UTF-8 encoding on standard output for safe Indic text printing on Windows
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

# ── Auto-refresh interval: 3 Hours (10800 seconds) ───────────────────
REFRESH_INTERVAL_SECONDS = 3 * 60 * 60  # 3 hours


def run_pipeline():
    """Execute the full FIR processing pipeline across all 5 target cities."""
    start_time = datetime.datetime.now()
    time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 70, flush=True)
    print(f"  MAHARASHTRA POLICE FIR PROCESSING PIPELINE", flush=True)
    print(f"  Execution Time: {time_str}", flush=True)
    print(f"  Target Cities : Pune | Mumbai Main | Thane | Nashik | Nagpur", flush=True)
    print("=" * 70, flush=True)

    # ── Step 1: Scraping Portal for the 5 Cities ─────────────────────
    print("\n[STEP 1/4] Scraping FIRs for the 5 Target Cities...", flush=True)
    download_dir = "firs_downloaded"
    scraper_res = scrape_firs(download_dir)
    if isinstance(scraper_res, tuple):
        download_dir, new_files = scraper_res
    else:
        download_dir, new_files = scraper_res, None

    # ── Step 2: Gemini LLM Structured Data Extraction ────────────────
    print("\n[STEP 2/4] Extracting Structured FIR Data with Google Gemini LLM...", flush=True)
    structured_records = process_pdfs(download_dir, target_files=new_files)

    if not structured_records:
        print("  [Warning] No records extracted. Continuing to next cycle.", flush=True)
        return

    print(f"  [Extraction Complete] Extracted {len(structured_records)} structured FIR records.", flush=True)

    # ── Step 3: Agentic Layer (Crime Classification + Geocoding) ─────
    print("\n[STEP 3/4] Agentic Processing Layer...", flush=True)
    print("  - LLM Multi-label Crime Classification (Google Gemini)", flush=True)
    print("  - Geographic Coordinates Resolution (OpenStreetMap Nominatim)", flush=True)
    enhanced_records = process_agentic_layer(structured_records)

    # Print summary of enhanced records for all 5 cities
    print("\n  Summary of Processed FIR Records by City:", flush=True)
    for i, r in enumerate(enhanced_records, 1):
        loc = r.get("location", "N/A")
        tags = r.get("crime_tags", [])
        coords = r.get("coordinates", {})
        fir_no = r.get("fir_number", "N/A")
        coord_str = f"Lat: {coords.get('lat')}, Lng: {coords.get('lng')}" if coords else "Coords: Not Resolved"
        clean_loc = str(loc)[:35].encode('ascii', 'replace').decode('ascii')
        print(f"    {i}. FIR #{fir_no:<10} | Loc: {clean_loc:<35} | Tags: {tags} | {coord_str}", flush=True)

    # ── Step 4: Supabase PostgreSQL Database Storage ────────────────
    print("\n[STEP 4/4] Storing Processed FIR Records into Supabase...", flush=True)
    success = save_to_database(enhanced_records)

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 70, flush=True)
    print(f"  Pipeline cycle completed successfully in {elapsed:.1f} seconds.", flush=True)
    print("=" * 70, flush=True)


def main():
    """
    Main entry point:
    1. Runs the FIR pipeline immediately for the 5 cities.
    2. Automatically refreshes itself every 3 hours (or runs once if --once is passed).
    """
    run_once = "--once" in sys.argv

    print("+-------------------------------------------------------------------+", flush=True)
    print("|   MAHARASHTRA POLICE FIR AUTOMATED MONITORING SYSTEM              |", flush=True)
    print("|   Cities: Pune | Mumbai Main | Thane | Nashik | Nagpur             |", flush=True)
    if run_once:
        print("|   Execution Mode: Single Run (--once flag detected)               |", flush=True)
    else:
        print("|   Refresh Schedule: Every 3 Hours                                 |", flush=True)
    print("+-------------------------------------------------------------------+", flush=True)

    cycle = 0
    while True:
        cycle += 1
        print(f"\n>>>> Starting Pipeline Run #{cycle} <<<<", flush=True)

        try:
            run_pipeline()
        except Exception as e:
            print(f"[Error] Pipeline encountered an exception: {e}", flush=True)
            import traceback
            traceback.print_exc()

        if run_once:
            print("\n[Done] Pipeline single execution completed (--once). Exiting cleanly.", flush=True)
            break

        next_run = datetime.datetime.now() + datetime.timedelta(seconds=REFRESH_INTERVAL_SECONDS)
        print(f"\n[TIMER] Next auto-refresh scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"[TIMER] Sleeping for {REFRESH_INTERVAL_SECONDS // 3600} hours ({REFRESH_INTERVAL_SECONDS} seconds)...", flush=True)
        time.sleep(REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
