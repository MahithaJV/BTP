import json
from database import get_supabase_client

sb = get_supabase_client()
r = sb.table("fir_records").select("id, fir_number, coordinates, location, crime_tags").execute()
records = r.data or []
total = len(records)
with_coords = 0
no_coords_list = []

for rec in records:
    coords = rec.get("coordinates")
    if isinstance(coords, str):
        try:
            coords = json.loads(coords)
        except:
            coords = None
    if coords and isinstance(coords, dict) and coords.get("lat"):
        with_coords += 1
    else:
        no_coords_list.append(rec)

print(f"Total records: {total}")
print(f"With coordinates (heat points ready): {with_coords}")
print(f"Without coordinates: {len(no_coords_list)}")
if no_coords_list:
    print("\nRecords missing coordinates:")
    for rec in no_coords_list:
        print(f"  - FIR #{rec.get('fir_number')}: Location={rec.get('location', 'N/A')}")
