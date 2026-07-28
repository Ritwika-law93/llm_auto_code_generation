# E-commerce Order Service

Build a backend service for an e-commerce order workflow:
- Product catalog with SKU, price, inventory count
- Shopping cart per authenticated user
- Place an order from a cart; deduct inventory atomically
- Order states: pending -> paid -> shipped -> delivered -> cancelled
- Webhook endpoint to receive payment confirmation from a payment provider
- Idempotent order creation (same client request id must not create duplicates)
- REST API with role-based access (customer vs admin)
