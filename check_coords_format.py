import json
from database import get_supabase_client

sb = get_supabase_client()
# Check the 4 records that were just updated
firs = ["0248/2026", "0401/2026", "0312/2026", "0189/2026"]
for fir in firs:
    r = sb.table("fir_records").select("fir_number, coordinates").eq("fir_number", fir).execute()
    if r.data:
        rec = r.data[0]
        coords = rec.get("coordinates")
        print(f"FIR #{fir}:")
        print(f"  Type: {type(coords)}")
        print(f"  Value: {coords}")
        print()
