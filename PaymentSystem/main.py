import stripe
import uvicorn as uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import aiohttp
import os

app = FastAPI()

# Database Connection
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    #payment_method = Column(String)
    provider = Column(String)
    payment_intent_id= Column(String) # user payment id


# Create Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Payment Request Model
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"
    #payment_method: str
    provider: str  # Options: 'paypal', 'stripe', 'wechat', 'alipay'
    payment_intent_id: str # random user str

# 🌍 Home Route
@app.get("/")
async def home():
    return {"message": "Welcome to the Payment API"}

# ✅ PayPal Payment
@app.post("/pay/paypal")
async def pay_paypal(request: PaymentRequest, db: Session = Depends(get_db)):
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "your_paypal_client_id")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "your_paypal_client_secret")
    PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"

    async with aiohttp.ClientSession() as session:
        # Get PayPal Access Token
        auth = aiohttp.BasicAuth(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        async with session.post(f"{PAYPAL_API_URL}/v1/oauth2/token", data={"grant_type": "client_credentials"}, auth=auth) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="PayPal authentication failed")
            data = await response.json()
            access_token = data.get("access_token")

        # Create PayPal Payment Order
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        json_data = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": request.currency, "value": str(request.amount)}}]
        }
        async with session.post(f"{PAYPAL_API_URL}/v2/checkout/orders", headers=headers, json=json_data) as response:
            return await response.json()

# ✅ Stripe Payment
@app.post("/pay/stripe")
async def pay_stripe(request: PaymentRequest, db: Session = Depends(get_db)):
    try:
        # STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "your_stripe_secret_key")
        STRIPE_SECRET_KEY = "sk_test_51R89YBCDPAHogqUvSbGqSjkrKFkXqqLjZ20ewF9uncNgriITD6HcLORXQplFhZ8NdONqpNhh3Z2epd63HoZuVes200bhd162e1"
        STRIPE_API_URL = "https://api.stripe.com/v1/payment_intents"

        headers = {"Authorization": f"Bearer {STRIPE_SECRET_KEY}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"amount": int(request.amount * 100), "currency": request.currency}

        async with aiohttp.ClientSession() as session:
            async with session.post(STRIPE_API_URL, headers=headers, data=data) as response:
                # # Assuming you have a Payment model that you want to save
                ind = await response.json()
                print("Full response:", ind, '\n')
                print(ind["id"] , '\n')

                new_payment = Payment(
                    provider="Stripe",
                    amount=data["amount"],  # Example amount from the response
                    currency="USD",  # Example currency from the response
                    payment_intent_id = ind["id"]  # payment_intent_id from Stripe response
                )

                # Add the new payment to the database session and commit
                db.add(new_payment)
                db.commit()
                db.refresh(new_payment)

                return await response.json()

    except Exception as e:
        db.rollback()  # Rollback if there's an error
        raise HTTPException(status_code=500, detail=str(e))


# from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# Your Stripe secret key
# stripe.api_key = 'sk_test_51R89YBCDPAHogqUvSbGqSjkrKFkXqqLjZ20ewF9uncNgriITD6HcLORXQplFhZ8NdONqpNhh3Z2epd63HoZuVes200bhd162e1'
#
# app = FastAPI()

# Request model for the payment details
# class PaymentRequest(BaseModel):
#     amount: float
#     currency: str = "usd"
#     payment_method: str = "card"  # default to 'card'

# @app.post("/pay/stripe")
# async def create_payment_intent(request: PaymentRequest):
#     try:
#         # Create a PaymentIntent with the amount and currency provided
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(request.amount * 100),  # Stripe expects amount in cents
#             currency=request.currency,
#             payment_method_types=[request.payment_method]
#         )
#         return JSONResponse(content={
#             "client_secret": payment_intent.client_secret,
#             "payment_intent_id": payment_intent.id
#         })
#     except stripe.error.StripeError as e:
#         raise HTTPException(status_code=400, detail=str(e))

@app.post("/pay/stripe/confirm")
async def confirm_payment(payment_intent_id: str, payment_method_id: str):
    try:
        # Confirm the PaymentIntent with the payment method provided
        payment_intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method_id
        )
        if payment_intent.status == "succeeded":
            return {"status": "Payment succeeded", "payment_intent": payment_intent.id}
        else:
            return {"status": "Payment failed", "payment_intent": payment_intent.id}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stripe Payment API!"}

# ✅ WeChat Pay (Placeholder)
@app.post("/pay/wechat")
async def pay_wechat(request: PaymentRequest, db: Session = Depends(get_db)):
    return {"message": f"WeChat payment of {request.amount} {request.currency} processed"}

# ✅ Alipay (Placeholder)
@app.post("/pay/alipay")
async def pay_alipay(request: PaymentRequest, db: Session = Depends(get_db)):
    return {"message": f"Alipay payment of {request.amount} {request.currency} processed"}

# ✅ General Payment Route (Calls Specific Method)
# @app.post("/pay/{payment_method}")
# async def process_payment(payment_method: str, request: PaymentRequest, db: Session = Depends(get_db)):
#     # Store Payment in Database
#     payment = Payment(amount=request.amount, currency=request.currency, payment_method=payment_method)
#     db.add(payment)
#     db.commit()
#     db.refresh(payment)
#
#     # Call the correct payment provider function
#     if payment_method == "paypal":
#         return await pay_paypal(request, db)
#     elif payment_method == "stripe":
#         return await pay_stripe(request, db)
#     elif payment_method == "wechat":
#         return await pay_wechat(request, db)
#     elif payment_method == "alipay":
#         return await pay_alipay(request, db)
#     else:
#         raise HTTPException(status_code=400, detail="Invalid payment method")

# ✅ Get Payment Transactions
@app.get("/transactions")
async def get_transactions(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return payments

# 🚀 Run FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
