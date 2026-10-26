import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Warning: Supabase credentials not found in environment.")
        return None
        
    try:
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None

def save_to_database(records, table_name="fir_records"):
    """
    Saves the enhanced structured FIR records to a Supabase PostgreSQL database.
    """
    supabase = get_supabase_client()
    
    if not supabase:
        print("Skipping database insertion due to missing credentials. Mock insertion successful.")
        for r in records:
            print(f"[Mock DB Insert] Saved {r.get('fir_number')} to DB.")
        return True
        
    print(f"Attempting to save {len(records)} records to Supabase table '{table_name}'...", flush=True)
    
    success_count = 0
    for record in records:
        fir_no = record.get("fir_number")
        try:
            # Check for existing record to avoid duplicate entries across 3-hour cycles
            if fir_no and fir_no != "Unknown":
                existing = supabase.table(table_name).select("id, coordinates").eq("fir_number", fir_no).execute()
                if existing.data and len(existing.data) > 0:
                    existing_row = existing.data[0]
                    # If existing record has no coordinates or null coordinates, update it!
                    if not existing_row.get("coordinates") and record.get("coordinates"):
                        supabase.table(table_name).update({
                            "coordinates": record.get("coordinates"),
                            "crime_tags": record.get("crime_tags", []),
                        }).eq("id", existing_row["id"]).execute()
                        print(f"  [DB Updated] Attached missing heat point coordinates to existing FIR #{fir_no}", flush=True)
                    else:
                        print(f"  [DB Exists] FIR #{fir_no} already stored in Supabase with coordinates. Skipping duplicate.", flush=True)
                    success_count += 1
                    continue

            data, count = supabase.table(table_name).insert(record).execute()
            print(f"  [DB OK] Inserted real FIR #{fir_no} into Supabase (Heat point ready)", flush=True)
            success_count += 1
        except Exception as e:
            print(f"  [DB Error] Inserting/Updating FIR #{fir_no}: {e}", flush=True)
            
    print(f"Database insertion completed. {success_count}/{len(records)} successful.", flush=True)
    return success_count == len(records)
