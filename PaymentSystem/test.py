import stripe

# Set your secret key
stripe.api_key = "sk_test_51R89YBCDPAHogqUvSbGqSjkrKFkXqqLjZ20ewF9uncNgriITD6HcLORXQplFhZ8NdONqpNhh3Z2epd63HoZuVes200bhd162e1"

# Create a payment intent
payment_intent = stripe.PaymentIntent.create(
    amount=5000,  # Amount in the smallest currency unit (e.g., cents)
    currency="usd",
)

print(payment_intent)