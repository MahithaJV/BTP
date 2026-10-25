"""
Utility script to reclassify all existing records in Supabase 'fir_records'
table using the 25 official multi-label crime categories.
"""
import time
from database import get_supabase_client
from agent import classify_crime, CRIME_CATEGORIES

def reclassify_all_records():
    supabase = get_supabase_client()
    if not supabase:
        print("Could not connect to Supabase. Check your .env file.")
        return

    print("Fetching records from Supabase table 'fir_records'...", flush=True)
    response = supabase.table("fir_records").select("id, fir_number, description, crime_tags").execute()
    records = response.data or []
    print(f"Found {len(records)} records to examine.\n", flush=True)

    updated_count = 0
    for r in records:
        rec_id = r.get("id")
        fir_no = r.get("fir_number")
        desc = r.get("description", "")
        old_tags = r.get("crime_tags", [])

        if not desc:
            continue

        new_tags = classify_crime(desc)
        valid_tags = [t for t in new_tags if t in CRIME_CATEGORIES]

        print(f"FIR #{fir_no} (ID: {rec_id}):")
        print(f"  Old Tags: {old_tags}")
        print(f"  New Tags: {valid_tags}")

        if valid_tags != old_tags:
            try:
                supabase.table("fir_records").update({"crime_tags": valid_tags}).eq("id", rec_id).execute()
                print("  [Updated in DB]", flush=True)
                updated_count += 1
            except Exception as e:
                print(f"  [Update Error] {e}", flush=True)
        else:
            print("  [Unchanged]", flush=True)
        print("-" * 50)
        time.sleep(0.5)

    print(f"\nReclassification complete! Updated {updated_count} record(s).")

if __name__ == "__main__":
    reclassify_all_records()
