import json
from database import get_supabase_client

def view_records():
    supabase = get_supabase_client()
    if not supabase:
        print("Could not connect to Supabase. Check your .env file.")
        return
        
    response = supabase.table("fir_records").select("*").execute()
    records = response.data
    
    print(f"\n=== Found {len(records)} Record(s) in Supabase 'fir_records' Table ===\n")
    for i, r in enumerate(records, 1):
        print(f"Record #{i}:")
        print(json.dumps(r, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    view_records()
