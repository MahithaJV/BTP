import json
from database import get_supabase_client
from agent import geocode_location
import time

sb = get_supabase_client()

# Get ALL records
r = sb.table("fir_records").select("*").execute()
records = r.data or []

print(f"Total records: {len(records)}\n")

missing = []
for rec in records:
    coords = rec.get("coordinates")
    fir_no = rec.get("fir_number", "?")
    loc = rec.get("location", "N/A")
    rec_id = rec.get("id")
    
    has_coords = bool(coords and isinstance(coords, dict) and coords.get("lat"))
    status = "OK" if has_coords else "MISSING"
    print(f"  ID={rec_id} | FIR #{fir_no} | coords={status} | loc={str(loc)[:60]}")
    
    if not has_coords:
        missing.append(rec)

print(f"\n{len(missing)} records need coordinates. Fixing now...\n")

for rec in missing:
    rec_id = rec.get("id")
    fir_no = rec.get("fir_number", "?")
    location = rec.get("location", "")
    
    print(f"Geocoding FIR #{fir_no} (ID={rec_id}): {location}")
    coords = geocode_location(location)
    print(f"  Got coordinates: {coords}")
    
    if coords and coords.get("lat") and coords.get("lng"):
        try:
            result = sb.table("fir_records").update(
                {"coordinates": {"lat": coords["lat"], "lng": coords["lng"]}}
            ).eq("id", rec_id).execute()
            print(f"  Update result: {result.data}")
        except Exception as e:
            print(f"  Error: {e}")
    
    time.sleep(1)

# Verify
print("\n--- Verification ---")
r2 = sb.table("fir_records").select("id, fir_number, coordinates").execute()
for rec in r2.data or []:
    coords = rec.get("coordinates")
    has = bool(coords and isinstance(coords, dict) and coords.get("lat"))
    print(f"  FIR #{rec.get('fir_number')} -> coords={'OK' if has else 'MISSING'}: {coords}")
