import re
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="IBAN Validator API", version="1.0.0")

# Simple in-memory rate limiting
request_counts = {}

def get_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return api_key

def check_rate_limit(api_key: str = Depends(get_api_key)):
    import time
    key = f"{api_key}:{int(time.time() // 60)}"
    request_counts[api_key] = request_counts.get(api_key, 0) + 1
    if request_counts[api_key] > 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return api_key

class IBANRequest(BaseModel):
    iban: str

class IBANResponse(BaseModel):
    iban: str
    is_valid: bool
    country_code: Optional[str]
    country_name: Optional[str]
    formatted: Optional[str]
    length: int
    error: Optional[str]

COUNTRY_CODES = {
    "AL": "Albania", "AD": "Andorra", "AT": "Austria", "AZ": "Azerbaijan",
    "BH": "Bahrain", "BE": "Belgium", "BA": "Bosnia and Herzegovina", "BR": "Brazil",
    "BG": "Bulgaria", "CR": "Costa Rica", "HR": "Croatia", "CY": "Cyprus",
    "CZ": "Czech Republic", "DK": "Denmark", "DO": "Dominican Republic", "EE": "Estonia",
    "FO": "Faroe Islands", "FI": "Finland", "FR": "France", "GE": "Georgia",
    "DE": "Germany", "GI": "Gibraltar", "GR": "Greece", "GL": "Greenland",
    "GT": "Guatemala", "HU": "Hungary", "IS": "Iceland", "IE": "Ireland",
    "IL": "Israel", "IT": "Italy", "JO": "Jordan", "KZ": "Kazakhstan",
    "KW": "Kuwait", "LV": "Latvia", "LB": "Lebanon", "LI": "Liechtenstein",
    "LT": "Lithuania", "LU": "Luxembourg", "MK": "Macedonia", "MT": "Malta",
    "MR": "Mauritania", "MU": "Mauritius", "MC": "Monaco", "MD": "Moldova",
    "ME": "Montenegro", "NL": "Netherlands", "NO": "Norway", "PK": "Pakistan",
    "PS": "Palestine", "PL": "Poland", "PT": "Portugal", "QA": "Qatar",
    "RO": "Romania", "SM": "San Marino", "SA": "Saudi Arabia", "RS": "Serbia",
    "SK": "Slovakia", "SI": "Slovenia", "ES": "Spain", "SE": "Sweden",
    "CH": "Switzerland", "TL": "Timor-Leste", "TN": "Tunisia", "TR": "Turkey",
    "AE": "United Arab Emirates", "GB": "United Kingdom", "VG": "Virgin Islands"
}

def validate_iban(iban: str) -> dict:
    cleaned = re.sub(r'\s+', '', iban.upper())
    
    if not re.match(r'^[A-Z]{2}[0-9A-Z]+$', cleaned):
        return {"is_valid": False, "error": "Invalid format: must start with 2 letters followed by alphanumeric characters"}
    
    length = len(cleaned)
    country_code = cleaned[:2]
    
    expected_lengths = {
        "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BE": 16, "BA": 20, "BR": 29,
        "BG": 22, "CR": 22, "HR": 21, "CY": 28, "CZ": 24, "DK": 18, "DO": 28, "EE": 20,
        "FO": 18, "FI": 18, "FR": 27, "GE": 22, "DE": 22, "GI": 23, "GR": 27, "GL": 18,
        "GT": 28, "HU": 28, "IS": 26, "IE": 22, "IL": 23, "IT": 27, "JO": 30, "KZ": 20,
        "KW": 30, "LV": 21, "LB": 28, "LI": 21, "LT": 20, "LU": 20, "MK": 19, "MT": 31,
        "MR": 27, "MU": 30, "MC": 27, "MD": 24, "ME": 22, "NL": 18, "NO": 15, "PK": 24,
        "PS": 29, "PL": 28, "PT": 25, "QA": 29, "RO": 24, "SM": 27, "SA": 24, "RS": 22,
        "SK": 24, "SI": 19, "ES": 24, "SE": 24, "CH": 21, "TL": 23, "TN": 24, "TR": 26,
        "AE": 23, "GB": 22, "VG": 24
    }
    
    if length != expected_lengths.get(country_code):
        return {"is_valid": False, "error": f"Invalid length for {country_code}. Expected {expected_lengths.get(country_code)}"}
    
    # Move first 4 chars to end and convert letters to numbers
    rearranged = cleaned[4:] + cleaned[:4]
    numeric = ''
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - ord('A') + 10)
        else:
            numeric += char
    
    # Mod 97 check
    remainder = int(numeric) % 97
    is_valid = remainder == 1
    
    formatted = ' '.join(cleaned[i:i+4] for i in range(0, len(cleaned), 4))
    
    return {
        "is_valid": is_valid,
        "country_code": country_code,
        "country_name": COUNTRY_CODES.get(country_code),
        "formatted": formatted,
        "error": None if is_valid else "Invalid checksum"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate", dependencies=[Depends(check_rate_limit)])
def validate_iban_endpoint(request: IBANRequest):
    if not request.iban:
        raise HTTPException(status_code=400, detail="IBAN is required")
    
    result = validate_iban(request.iban)
    return IBANResponse(
        iban=re.sub(r'\s+', '', request.iban.upper()),
        **result
    )

@app.get("/countries")
def get_countries():
    return {"countries": COUNTRY_CODES}

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    pass
