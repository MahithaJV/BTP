"""
FastAPI REST API server for the Crime Dashboard.
Connects to Supabase and serves FIR records + analytics to the React frontend.
"""
import os
import json
from datetime import datetime
from collections import Counter
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Crime Watch Maharashtra FIR API",
    description="FastAPI REST API serving FIR records and crime analytics from Supabase",
    version="1.0.0",
)

# ── Enable CORS for frontend integration ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase client ──────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_supabase() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Helpers ──────────────────────────────────────────────────────────
def parse_crime_tags(raw):
    """Parse crime_tags from various DB formats into a flat list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            return [t.strip() for t in raw.split(",") if t.strip()]
    return []


# ── API Routes ───────────────────────────────────────────────────────
@app.get("/")
def root():
    """Root info endpoint."""
    return {
        "name": "Crime Watch Maharashtra FIR API",
        "status": "online",
        "framework": "FastAPI",
        "docs_url": "/docs",
    }


@app.get("/api/records")
def get_records(
    city: Optional[str] = Query(None, description="Filter by city name"),
    crime: Optional[str] = Query(None, description="Filter by crime category"),
    limit: Optional[int] = Query(None, description="Limit number of returned records"),
):
    """Get all FIR records with optional filtering."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select("*").execute()
        records = response.data or []

        # Normalize each record for the frontend
        normalized = []
        for r in records:
            coords = r.get("coordinates")
            if isinstance(coords, str):
                try:
                    coords = json.loads(coords)
                except (json.JSONDecodeError, TypeError):
                    coords = None

            tags = parse_crime_tags(r.get("crime_tags", []))

            record_item = {
                "id": r.get("id"),
                "fir_number": r.get("fir_number", "Unknown"),
                "date": r.get("date", ""),
                "location": r.get("location", "Unknown"),
                "description": r.get("description", ""),
                "complainant": r.get("complainant", "Anonymous"),
                "accused": r.get("accused", "Unknown"),
                "crime_tags": tags,
                "coordinates": coords,
                "created_at": r.get("created_at", ""),
            }

            # Optional query parameter filtering
            if city and city.lower() != "all":
                if city.lower() not in str(record_item["location"]).lower():
                    continue
            if crime and crime.lower() != "all":
                if not any(crime.lower() in str(t).lower() for t in tags):
                    continue

            normalized.append(record_item)

        if limit and limit > 0:
            normalized = normalized[:limit]

        return {"records": normalized, "total": len(normalized)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/statistics")
def get_statistics():
    """Aggregate crime statistics for dashboard cards."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select("*").execute()
        records = response.data or []

        total_firs = len(records)
        geocoded_count = 0
        city_counter = Counter()
        tag_counter = Counter()
        today_count = 0
        today_str = datetime.now().strftime("%Y-%m-%d")

        for r in records:
            coords = r.get("coordinates")
            if isinstance(coords, str):
                try:
                    coords = json.loads(coords)
                except (json.JSONDecodeError, TypeError):
                    coords = None

            if coords and coords.get("lat") and coords.get("lng"):
                geocoded_count += 1

            tags = parse_crime_tags(r.get("crime_tags", []))
            for tag in tags:
                tag_counter[tag] += 1

            loc = r.get("location", "")
            for city in ["Pune", "Mumbai", "Thane", "Nashik", "Nagpur"]:
                if city.lower() in str(loc).lower():
                    city_counter[city] += 1
                    break

            date_str = r.get("date", "") or r.get("created_at", "")
            if today_str in str(date_str):
                today_count += 1

        return {
            "total_firs": total_firs,
            "geocoded_count": geocoded_count,
            "today_count": today_count,
            "cities": dict(city_counter),
            "top_crimes": dict(tag_counter.most_common(10)),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/crime-distribution")
def crime_distribution():
    """Crime category distribution for charts."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select("crime_tags").execute()
        records = response.data or []
        tag_counter = Counter()

        for r in records:
            tags = parse_crime_tags(r.get("crime_tags", []))
            for tag in tags:
                tag_counter[tag] += 1

            distribution = [
                {"category": cat, "count": cnt}
                for cat, cnt in tag_counter.most_common()
            ]
        return {"distribution": distribution}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/city-distribution")
def city_distribution():
    """FIR counts by city."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select("location").execute()
        records = response.data or []
        city_counter = Counter()

        for r in records:
            loc = r.get("location", "")
            matched = False
            for city in ["Pune", "Mumbai", "Thane", "Nashik", "Nagpur"]:
                if city.lower() in str(loc).lower():
                    city_counter[city] += 1
                    matched = True
                    break
            if not matched:
                city_counter["Other"] += 1

        distribution = [
            {"city": city, "count": cnt}
            for city, cnt in city_counter.most_common()
        ]
        return {"distribution": distribution}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/trend")
def crime_trend():
    """Time-based crime frequency trend (daily counts)."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select("date,created_at").execute()
        records = response.data or []
        date_counter = Counter()

        for r in records:
            raw_date = r.get("date", "") or ""
            # Try to parse various date formats
            parsed = None
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                try:
                    parsed = datetime.strptime(raw_date.strip(), fmt)
                    break
                except (ValueError, AttributeError):
                    continue

            if not parsed:
                # Fall back to created_at timestamp
                created_at = r.get("created_at", "")
                if created_at:
                    try:
                        parsed = datetime.fromisoformat(
                            str(created_at).replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        continue

            if parsed:
                date_key = parsed.strftime("%Y-%m-%d")
                date_counter[date_key] += 1

        # Sort by date and return
        trend = [
            {"date": d, "count": c}
            for d, c in sorted(date_counter.items())
        ]
        return {"trend": trend}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/heatmap-data")
def heatmap_data():
    """Returns lat/lng points with intensity for the heatmap layer."""
    supabase = get_supabase()
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})

    try:
        response = supabase.table("fir_records").select(
            "coordinates,crime_tags,location,fir_number,date"
        ).execute()
        records = response.data or []
        points = []

        for r in records:
            coords = r.get("coordinates")
            if isinstance(coords, str):
                try:
                    coords = json.loads(coords)
                except (json.JSONDecodeError, TypeError):
                    continue

            if not (coords and isinstance(coords, dict) and coords.get("lat") and coords.get("lng")):
                from agent import _city_centroid_fallback
                coords = _city_centroid_fallback(r.get("location", ""))

            if coords and coords.get("lat") and coords.get("lng"):
                tags = parse_crime_tags(r.get("crime_tags", []))
                # Intensity based on severity
                severity_map = {
                    "Murder": 1.0, "Attempt to Murder": 0.95,
                    "Rape": 0.95, "Kidnapping / Abduction": 0.9,
                    "Robbery": 0.85, "Human Trafficking": 0.9,
                    "Drug-related Offences": 0.8,
                    "Assault / Physical Attack": 0.75,
                }
                intensity = 0.5
                for tag in tags:
                    if tag in severity_map:
                        intensity = max(intensity, severity_map[tag])

                points.append({
                    "lat": float(coords["lat"]),
                    "lng": float(coords["lng"]),
                    "intensity": intensity,
                    "fir_number": r.get("fir_number", ""),
                    "location": r.get("location", ""),
                    "crime_tags": tags,
                    "date": r.get("date", ""),
                })

        return {"points": points, "total": len(points)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/health")
def health():
    """Health check endpoint."""
    supabase = get_supabase()
    connected = supabase is not None
    if connected:
        try:
            supabase.table("fir_records").select("id").limit(1).execute()
        except Exception:
            connected = False

    return {
        "status": "ok" if connected else "degraded",
        "database": "connected" if connected else "disconnected",
        "framework": "FastAPI",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CRIME DASHBOARD FASTAPI SERVER")
    print("  Serving FIR records from Supabase to React frontend")
    print("  Interactive API Docs: http://localhost:5000/docs")
    print("=" * 60)
    uvicorn.run("api_server:app", host="0.0.0.0", port=5000, reload=True)
