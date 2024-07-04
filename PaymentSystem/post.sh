#!/bin/bash

curl -X POST http://127.0.0.1:8000/pay/stripe \
-H "Content-Type: application/json" \
-d '{
    "amount": 50.0,
    "currency": "USD",
    "payment_method": "card_1HfJs2JlDZv0R9KqECq1jswt",
    "provider": "Stripe"
}'