import os
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
# Bridge env var: langchain-google-genai expects GOOGLE_API_KEY
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

import re

# ── The 25 Official Crime Categories for Multi-Label Classification ──
CRIME_CATEGORIES = [
    "Theft",
    "Burglary / Housebreaking",
    "Robbery",
    "Snatching",
    "Vehicle Theft",
    "Cheating / Fraud",
    "Cybercrime",
    "Online Financial Fraud",
    "Assault / Physical Attack",
    "Murder",
    "Attempt to Murder",
    "Kidnapping / Abduction",
    "Missing Person",
    "Rape",
    "Sexual Harassment",
    "Stalking",
    "Domestic Violence / Cruelty",
    "Dowry-related Offences",
    "Criminal Intimidation",
    "Criminal Trespass",
    "Property Damage / Vandalism",
    "Forgery / Document Fraud",
    "Bribery / Corruption",
    "Drug-related Offences",
    "Human Trafficking",
]

_CATEGORIES_FORMATTED_FOR_PROMPT = "\n".join(
    f"{i + 1}. {cat}" for i, cat in enumerate(CRIME_CATEGORIES)
)

_CLASSIFICATION_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """You are an expert police First Information Report (FIR) crime classification system in India.
Analyze the following police FIR incident description and perform multi-label classification.

You MUST choose one or more categories STRICTLY and ONLY from this predefined list of 25 crime categories:
"""
    + _CATEGORIES_FORMATTED_FOR_PROMPT
    + """

STRICT RULES:
1. Multi-label: A single incident can be assigned multiple applicable categories (e.g., both "Snatching" and "Robbery", or both "Online Financial Fraud" and "Cybercrime").
2. Predefined only: Do NOT invent, extrapolate, or return any category outside the 25 listed above.
3. Formatting: Return ONLY the exact category names separated by commas. Do not include category numbers, bullet points, explanations, or extra tags.

Description:
{description}

Categories:"""
)


def _normalize_category(tag_str):
    """
    Normalizes raw LLM output or variation strings into the exact canonical category name
    from the 25 allowed categories. Returns None if no valid match.
    """
    if not tag_str:
        return None

    # Strip prefixes like "1.", "1)", "- ", "* ", "Tags:", "Categories:"
    clean = re.sub(
        r"^(?:(?:categories|tags|category)\s*[:\.]?|\d+[\.\)\:\-]*|\*+|\-+)\s*",
        "",
        tag_str.strip(),
        flags=re.IGNORECASE,
    ).strip()
    clean = clean.strip("\"'`").strip()
    if not clean:
        return None

    # 1. Exact case-insensitive match
    for cat in CRIME_CATEGORIES:
        if clean.lower() == cat.lower():
            return cat

    # 2. Match with slash variations (e.g., "Burglary/Housebreaking" -> "Burglary / Housebreaking")
    clean_normalized_slash = re.sub(r"\s*/\s*", " / ", clean)
    for cat in CRIME_CATEGORIES:
        if clean_normalized_slash.lower() == cat.lower():
            return cat

    # 3. Match single components of dual-term categories (e.g. "Burglary" -> "Burglary / Housebreaking")
    for cat in CRIME_CATEGORIES:
        if " / " in cat:
            parts = [p.strip().lower() for p in cat.split(" / ")]
            if clean.lower() in parts:
                return cat

    # 4. Standard aliases and common spelling variations
    aliases = {
        "cyber crime": "Cybercrime",
        "online fraud": "Online Financial Fraud",
        "financial fraud": "Online Financial Fraud",
        "bank fraud": "Online Financial Fraud",
        "attempted murder": "Attempt to Murder",
        "dowry": "Dowry-related Offences",
        "dowry harassment": "Dowry-related Offences",
        "dowry death": "Dowry-related Offences",
        "dowry offences": "Dowry-related Offences",
        "dowry offenses": "Dowry-related Offences",
        "dowry-related offenses": "Dowry-related Offences",
        "intimidation": "Criminal Intimidation",
        "trespass": "Criminal Trespass",
        "vandalism": "Property Damage / Vandalism",
        "property damage": "Property Damage / Vandalism",
        "document fraud": "Forgery / Document Fraud",
        "forgery": "Forgery / Document Fraud",
        "bribery": "Bribery / Corruption",
        "corruption": "Bribery / Corruption",
        "drugs": "Drug-related Offences",
        "drug offences": "Drug-related Offences",
        "drug offenses": "Drug-related Offences",
        "drug-related offenses": "Drug-related Offences",
        "narcotics": "Drug-related Offences",
        "trafficking": "Human Trafficking",
    }
    return aliases.get(clean.lower(), None)


def _keyword_classify_fallback(description):
    """
    Intelligent rule-based multi-label classification strictly conforming to
    the 25 predefined categories when LLM is unavailable or unparseable.
    """
    desc_lower = description.lower()
    tags = []

    # 1. Attempt to Murder vs Murder
    if any(k in desc_lower for k in ["attempt to murder", "attempted murder", "tried to kill", "307 ipc", "section 307"]):
        tags.append("Attempt to Murder")
    elif any(k in desc_lower for k in ["murder", "murdered", "homicide", "stabbed to death", "dead body found", "302 ipc", "section 302", "killed"]):
        tags.append("Murder")

    # 2. Assault / Physical Attack
    if any(k in desc_lower for k in [
        "assault", "assaulted", "physical attack", "beaten", "attacked", "hit with",
        "stone", "iron rod", "sticks", "blows", "head injury", "sustained injuries",
        "fracture", "grievous hurt", "323", "324", "326"
    ]):
        tags.append("Assault / Physical Attack")

    # 3. Vehicle Theft vs Theft vs Burglary / Housebreaking vs Snatching vs Robbery
    is_vehicle = any(k in desc_lower for k in [
        "scooter", "motorcycle", "bike", "car", "auto rickshaw", "two wheeler",
        "four wheeler", "vehicle", "suzuki", "honda", "hero", "pulsar", "activa"
    ])

    if any(k in desc_lower for k in ["snatch", "snatched", "snatching", "chain snatch", "purse snatch"]):
        tags.append("Snatching")

    if any(k in desc_lower for k in ["robbery", "robbed", "looted", "dacoity", "at gunpoint", "knifepoint", "forcibly took", "392", "394", "395", "397"]):
        tags.append("Robbery")

    if any(k in desc_lower for k in ["burglary", "housebreaking", "broken into", "broke into", "lock broken", "shutter broken", "entered house", "night break", "454", "457"]):
        tags.append("Burglary / Housebreaking")

    if is_vehicle and any(k in desc_lower for k in ["theft", "stole", "stolen", "parked at", "missing", "379"]):
        tags.append("Vehicle Theft")

    if any(k in desc_lower for k in ["theft", "stole", "stolen", "stealing", "pickpocket", "laptop", "gold", "ornament", "purse", "wallet", "cash"]):
        tags.append("Theft")

    # 4. Online Financial Fraud vs Cybercrime vs Cheating / Fraud
    has_online_finance = any(k in desc_lower for k in [
        "otp", "kyc", "bank fraud", "debit card", "credit card", "upi",
        "unauthorized transaction", "online fraud", "part-time job scam",
        "telegram scam", "fraudulent debit", "phishing"
    ])
    if has_online_finance:
        tags.append("Online Financial Fraud")
        tags.append("Cybercrime")
    elif any(k in desc_lower for k in ["cyber", "hacked", "hacking", "malware", "social media account", "unauthorized access"]):
        tags.append("Cybercrime")

    if any(k in desc_lower for k in ["cheat", "cheated", "cheating", "fraud", "deceived", "fake promise", "investment", "embezzl", "420 ipc", "section 420"]):
        tags.append("Cheating / Fraud")

    # 5. Forgery / Document Fraud
    if any(k in desc_lower for k in ["forgery", "forged", "fake document", "counterfeit", "bogus document", "fabricated", "fake stamp", "465", "467", "468", "471"]):
        tags.append("Forgery / Document Fraud")

    # 6. Kidnapping / Abduction vs Missing Person
    if any(k in desc_lower for k in ["kidnap", "kidnapped", "kidnapping", "abduct", "abducted", "abduction", "ransom", "hostage", "363", "364", "365"]):
        tags.append("Kidnapping / Abduction")
    if any(k in desc_lower for k in ["missing", "untraceable", "did not return", "went missing", "whereabouts unknown", "disappeared"]):
        tags.append("Missing Person")

    # 7. Rape vs Sexual Harassment vs Stalking
    if any(k in desc_lower for k in ["rape", "raped", "gang rape", "gangrape", "section 376", "376 ipc"]):
        tags.append("Rape")
    if any(k in desc_lower for k in ["sexual harassment", "molest", "molested", "molestation", "outraging modesty", "eve teasing", "section 354", "354 ipc"]):
        tags.append("Sexual Harassment")
    if any(k in desc_lower for k in ["stalk", "stalking", "stalked", "following continuously", "section 354d"]):
        tags.append("Stalking")

    # 8. Domestic Violence / Cruelty vs Dowry-related Offences
    if any(k in desc_lower for k in ["dowry", "dahej", "dowry death", "dowry demand", "harassment for dowry", "304b"]):
        tags.append("Dowry-related Offences")
    if any(k in desc_lower for k in ["domestic violence", "cruelty by husband", "in-laws", "marital abuse", "498a", "section 498a"]):
        tags.append("Domestic Violence / Cruelty")

    # 9. Criminal Intimidation
    if any(k in desc_lower for k in ["threat", "threatened", "death threat", "intimidation", "dire consequences", "extortion", "506 ipc", "section 506"]):
        tags.append("Criminal Intimidation")

    # 10. Criminal Trespass
    if any(k in desc_lower for k in ["trespass", "criminal trespass", "unlawful entry", "illegal entry", "encroached", "447", "448"]):
        tags.append("Criminal Trespass")

    # 11. Property Damage / Vandalism
    if any(k in desc_lower for k in ["property damage", "vandalism", "damaged vehicle", "broken glass", "destroyed property", "mischief", "427 ipc"]):
        tags.append("Property Damage / Vandalism")

    # 12. Bribery / Corruption
    if any(k in desc_lower for k in ["bribe", "bribery", "corruption", "gratification", "anti-corruption", "prevention of corruption"]):
        tags.append("Bribery / Corruption")

    # 13. Drug-related Offences
    if any(k in desc_lower for k in ["drug", "narcotics", "ndps", "ganja", "charas", "heroin", "mephedrone", "md", "contraband"]):
        tags.append("Drug-related Offences")

    # 14. Human Trafficking
    if any(k in desc_lower for k in ["human trafficking", "trafficking", "trafficked", "sold for prostitution", "forced labor", "370 ipc"]):
        tags.append("Human Trafficking")

    # Deduplicate while preserving order and ensuring membership in CRIME_CATEGORIES
    seen = set()
    result = []
    for t in tags:
        if t in CRIME_CATEGORIES and t not in seen:
            seen.add(t)
            result.append(t)

    # If completely unclassified, assign default closest category from the 25
    if not result:
        result = ["Theft"]

    return result


def classify_crime(description):
    """
    Agentic task 1: Multi-label classification of the crime based on its description.
    Classifies strictly into the 25 predefined crime categories:
    1. Theft
    2. Burglary / Housebreaking
    3. Robbery
    4. Snatching
    5. Vehicle Theft
    6. Cheating / Fraud
    7. Cybercrime
    8. Online Financial Fraud
    9. Assault / Physical Attack
    10. Murder
    11. Attempt to Murder
    12. Kidnapping / Abduction
    13. Missing Person
    14. Rape
    15. Sexual Harassment
    16. Stalking
    17. Domestic Violence / Cruelty
    18. Dowry-related Offences
    19. Criminal Intimidation
    20. Criminal Trespass
    21. Property Damage / Vandalism
    22. Forgery / Document Fraud
    23. Bribery / Corruption
    24. Drug-related Offences
    25. Human Trafficking
    """
    if not description or not description.strip():
        return []

    if not os.environ.get("GEMINI_API_KEY"):
        return _keyword_classify_fallback(description)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=0,
            timeout=25,
            max_retries=1,
        )

        chain = _CLASSIFICATION_PROMPT_TEMPLATE | llm
        response = chain.invoke({"description": description})
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )

        # Parse tags from comma and/or newline separated output
        raw_items = [
            item.strip()
            for line in str(content).split("\n")
            for item in line.split(",")
            if item.strip()
        ]

        matched_tags = []
        for raw in raw_items:
            norm = _normalize_category(raw)
            if norm and norm in CRIME_CATEGORIES and norm not in matched_tags:
                matched_tags.append(norm)

        if matched_tags:
            return matched_tags

        # If LLM returned text that didn't match canonical names, use fallback
        return _keyword_classify_fallback(description)
    except Exception as e:
        print(f"  Classification notice ({e}), applying intelligent keyword fallback...", flush=True)
        return _keyword_classify_fallback(description)

# Guaranteed city and area centroids for the 5 target cities + key sub-localities
CITY_CENTROIDS = {
    "pune": {"lat": 18.5204, "lng": 73.8567},
    "mumbai": {"lat": 19.0760, "lng": 72.8777},
    "thane": {"lat": 19.2183, "lng": 72.9781},
    "nashik": {"lat": 19.9975, "lng": 73.7898},
    "nagpur": {"lat": 21.1458, "lng": 79.0882},
    "kalyan": {"lat": 19.2403, "lng": 73.1305},
    "bhiwandi": {"lat": 19.2813, "lng": 73.0483},
    "dadar": {"lat": 19.0178, "lng": 72.8478},
    "andheri": {"lat": 19.1136, "lng": 72.8697},
    "bhandup": {"lat": 19.1439, "lng": 72.9372},
    "sitabuldi": {"lat": 21.1466, "lng": 79.0806},
    "vadgaonsheri": {"lat": 18.5538, "lng": 73.9142},
    "lohiyanagar": {"lat": 18.5089, "lng": 73.8711},
    "shivajinagar": {"lat": 18.5314, "lng": 73.8446},
    "panchavati": {"lat": 20.0065, "lng": 73.7831},
    "beltarodi": {"lat": 21.0850, "lng": 79.0820},
}


def _city_centroid_fallback(location_name):
    """
    Guaranteed fallback to city or sub-area centroid with small deterministic jitter
    so heat points do not collapse to an identical single point.
    """
    import hashlib
    loc_lower = str(location_name or "").lower()

    # Check specific areas first, then main cities
    for place, coords in CITY_CENTROIDS.items():
        if place in loc_lower:
            h = int(hashlib.md5(str(location_name).encode("utf-8")).hexdigest(), 16)
            jitter_lat = ((h % 1000) / 1000.0 - 0.5) * 0.015
            jitter_lng = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.015
            return {
                "lat": round(coords["lat"] + jitter_lat, 6),
                "lng": round(coords["lng"] + jitter_lng, 6),
            }

    # Default Maharashtra center fallback
    return {"lat": 19.7515, "lng": 75.7139}


def geocode_location(location_name):
    """
    Agentic task 2: Geocoding the location using OpenStreetMap Nominatim.
    Falls back gracefully to city-level and guaranteed centroids so coordinates are NEVER None.
    """
    import urllib.parse
    import time

    if not location_name or not str(location_name).strip():
        return {"lat": 19.7515, "lng": 75.7139}

    # Generate progressive candidate queries
    candidates = [
        f"{location_name}, Maharashtra, India",
        location_name,
    ]

    # Try comma-separated sub-parts (e.g. 'Lohiyanagar, Pune' or 'Kalyan West, Thane')
    parts = [p.strip() for p in location_name.split(",") if p.strip()]
    if len(parts) > 1:
        candidates.append(", ".join(parts[1:]) + ", Maharashtra, India")
        candidates.append(parts[-1] + ", Maharashtra, India")

    # Check for target cities
    for city in ["Pune", "Mumbai", "Thane", "Nashik", "Nagpur"]:
        if city.lower() in location_name.lower():
            candidates.append(f"{city}, Maharashtra, India")
            break

    for candidate in candidates:
        try:
            query = urllib.parse.quote(candidate)
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            response = requests.get(
                url,
                headers={"User-Agent": "BTP-FIR-Pipeline/1.0 (CrimeWatch-Maharashtra)"},
                timeout=6,
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
            time.sleep(0.4)
        except Exception:
            continue

    # Guaranteed fallback: resolve to city/region centroid
    fallback_coords = _city_centroid_fallback(location_name)
    print(f"  [Geocoding Fallback] Using regional centroid for '{location_name}': {fallback_coords}", flush=True)
    return fallback_coords

def process_agentic_layer(records):
    """
    Enhances the structured records with crime classification and geocoding.
    """
    enhanced_records = []
    
    for record in records:
        print(f"  Agentic Layer processing for FIR: {record.get('fir_number', 'Unknown')}", flush=True)
        
        # 1. Classification
        description = record.get("description", "")
        if description:
            tags = classify_crime(description)
            record["crime_tags"] = tags
        else:
            record["crime_tags"] = []
            
        # 2. Geocoding
        location = record.get("location", "")
        if location:
            coordinates = geocode_location(location)
            record["coordinates"] = coordinates
        else:
            record["coordinates"] = None
            
        enhanced_records.append(record)
        
    return enhanced_records
