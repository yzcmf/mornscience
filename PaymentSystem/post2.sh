#!/bin/zsh

curl -X POST http://127.0.0.1:8000/pay/stripe \
-H "Content-Type: application/json" \
-d '{
    "amount": 20.0,
    "currency": "USD",
    "provider": "stripe",
    "payment_intent_id":"fsdfefwefwefew",
    "payment_method": "pm_card_visa"
}'
