# URL Shortener Service

Build a URL shortening service:
- POST a long URL, get back a short code (6-8 chars, base62)
- GET /{code} redirects (HTTP 301) to the original URL
- Custom alias support (user-provided code, must be unique)
- Optional expiry date per link
- Track click count and last-accessed timestamp per link
- Rate limit unauthenticated requests
- REST API with OpenAPI documentation
