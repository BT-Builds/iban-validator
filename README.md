# IBAN Validator API

Validate IBAN (International Bank Account Number) format, country, and checksum.

## Endpoints

### POST /validate
Validate an IBAN and get formatted result.

**Request:**
```json
{
  "iban": "GB82WEST12345698765432"
}
```

**Response:**
```json
{
  "iban": "GB82WEST12345698765432",
  "is_valid": true,
  "country_code": "GB",
  "country_name": "United Kingdom",
  "formatted": "GB82 WEST 1234 5698 7654 32",
  "error": null
}
```

### GET /countries
Get list of supported country codes.

**Response:**
```json
{
  "countries": {
    "GB": "United Kingdom",
    "DE": "Germany",
    ...
  }
}
```

### GET /health
Health check endpoint (no auth required).

## Example Usage

```bash
curl -X POST https://<slug>.vercel.app/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"iban": "GB82WEST12345698765432"}'
```

## Validation

The API validates:
1. Format (2 letter country code + alphanumeric)
2. Length per country standard
3. Mod-97 checksum

## Pricing
- Free tier: 100 requests/month
- $29/month: Unlimited requests, priority support