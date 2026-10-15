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
        
    print(f"Attempting to save {len(records)} records to Supabase table '{table_name}'...")
    
    success_count = 0
    for record in records:
        try:
            # Flatten or format the record to match your Supabase schema
            # Example: coordinates dict to lat/lng columns, lists to arrays, etc.
            
            # Simple insertion assuming JSON columns or matching schema
            data, count = supabase.table(table_name).insert(record).execute()
            print(f"Successfully inserted FIR: {record.get('fir_number')}")
            success_count += 1
        except Exception as e:
            print(f"Error inserting record {record.get('fir_number')}: {e}")
            
    print(f"Database insertion completed. {success_count}/{len(records)} successful.")
    return success_count == len(records)
