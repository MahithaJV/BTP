import os
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
# Bridge env var: langchain-google-genai expects GOOGLE_API_KEY
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

def classify_crime(description):
    """
    Agentic task 1: Multi-label classification of the crime based on its description.
    Uses Gemini LLM.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return ["Theft", "Property Crime"] # Mock classification
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    
    prompt = PromptTemplate.from_template(
        """Analyze the following police FIR description and classify the crime.
        Assign appropriate multi-label tags (e.g., Theft, Assault, Cybercrime, Fraud, Domestic Violence).
        Return the tags as a comma-separated list.
        
        Description:
        {description}
        
        Tags:"""
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"description": description})
        # Handle response.content being either a str or list of content parts
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        tags = [tag.strip() for tag in content.split(",")]
        return tags
    except Exception as e:
        print(f"Error during classification: {e}")
        return ["Unknown"]

def geocode_location(location_name):
    """
    Agentic task 2: Geocoding the location using Google Maps API.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_MAPS_API_KEY not found. Returning mock coordinates.")
        return {"lat": 18.9387, "lng": 72.8256} # Mock coordinates (Mumbai)
        
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location
        else:
            print(f"Geocoding API error: {data['status']}")
            return None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None

def process_agentic_layer(records):
    """
    Enhances the structured records with crime classification and geocoding.
    """
    enhanced_records = []
    
    for record in records:
        print(f"Agentic Layer processing for FIR: {record.get('fir_number', 'Unknown')}")
        
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
