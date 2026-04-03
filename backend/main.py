from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json, time, math, os
from algorand_service import AlgorandService

app = FastAPI(title="FreshDrop Pricing Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUCTS = [
    {"id": 1,  "name": "Protein Bar (Mango)",      "category": "Healthy Snacks", "mrp": 120, "cost": 72,  "targetMargin": 28, "stock": 80,  "soldPerDay": 8,  "shelfLife": 30, "daysRemaining": 6},
    {"id": 2,  "name": "Cold Press Orange Juice",   "category": "Fresh Juice",    "mrp": 90,  "cost": 52,  "targetMargin": 25, "stock": 45,  "soldPerDay": 12, "shelfLife": 7,  "daysRemaining": 2},
    {"id": 3,  "name": "Artisan Sourdough",         "category": "Bakery",         "mrp": 110, "cost": 58,  "targetMargin": 30, "stock": 30,  "soldPerDay": 15, "shelfLife": 5,  "daysRemaining": 1},
    {"id": 4,  "name": "Greek Yogurt Premium",      "category": "Dairy",          "mrp": 75,  "cost": 44,  "targetMargin": 22, "stock": 120, "soldPerDay": 20, "shelfLife": 14, "daysRemaining": 8},
    {"id": 5,  "name": "Makhana Roasted",           "category": "Healthy Snacks", "mrp": 180, "cost": 100, "targetMargin": 32, "stock": 60,  "soldPerDay": 5,  "shelfLife": 20, "daysRemaining": 11},
    {"id": 6,  "name": "Paneer Fresh 200g",         "category": "Dairy",          "mrp": 85,  "cost": 55,  "targetMargin": 20, "stock": 90,  "soldPerDay": 18, "shelfLife": 10, "daysRemaining": 4},
    {"id": 7,  "name": "Multigrain Bread",          "category": "Bakery",         "mrp": 65,  "cost": 35,  "targetMargin": 25, "stock": 50,  "soldPerDay": 10, "shelfLife": 5,  "daysRemaining": 2},
    {"id": 8,  "name": "Almond Milk 1L",            "category": "Dairy",          "mrp": 150, "cost": 95,  "targetMargin": 22, "stock": 35,  "soldPerDay": 7,  "shelfLife": 10, "daysRemaining": 3},
    {"id": 9,  "name": "Chicken Tikka Ready Meal",  "category": "Ready-to-eat",   "mrp": 220, "cost": 130, "targetMargin": 30, "stock": 25,  "soldPerDay": 8,  "shelfLife": 4,  "daysRemaining": 2},
    {"id": 10, "name": "Spinach & Kale Juice",      "category": "Fresh Juice",    "mrp": 110, "cost": 65,  "targetMargin": 28, "stock": 40,  "soldPerDay": 6,  "shelfLife": 5,  "daysRemaining": 1},
    {"id": 11, "name": "Baked Oat Cookies",         "category": "Healthy Snacks", "mrp": 95,  "cost": 52,  "targetMargin": 30, "stock": 70,  "soldPerDay": 9,  "shelfLife": 21, "daysRemaining": 14},
    {"id": 12, "name": "Cheddar Cheese Slice",      "category": "Dairy",          "mrp": 130, "cost": 80,  "targetMargin": 25, "stock": 55,  "soldPerDay": 11, "shelfLife": 21, "daysRemaining": 5},
]

CATEGORY_TRIGGERS = {
    "Dairy": 3, "Bakery": 2, "Fresh Juice": 2,
    "Ready-to-eat": 2, "Healthy Snacks": 7, "Regular Snacks": 14,
}

algo_service = AlgorandService()

class OptimizeRequest(BaseModel):
    id: int
    name: str
    category: str
    mrp: float
    cost: float
    targetMargin: float
    stock: int
    soldPerDay: float
    shelfLife: int
    daysRemaining: int

class OptimizeResponse(BaseModel):
    product_id: int
    product_name: str
    old_price: float
    optimal_price: float
    margin_pct: float
    expiry_score: float
    velocity_multiplier: float
    trigger_days: int
    is_triggered: bool
    min_price: float
    txid: Optional[str]
    explorer_url: Optional[str]
    algo_address: str
    timestamp: float

def calculate_expiry_score(days_remaining, shelf_life):
    urgency = 1 - (days_remaining / shelf_life)
    return round(min(max(urgency * 100, 0), 100), 2)

def calculate_velocity_multiplier(sold_per_day, stock, days_remaining):
    if days_remaining <= 0: return 0.70
    target_per_day = stock / days_remaining
    if target_per_day == 0: return 1.0
    ratio = sold_per_day / target_per_day
    if ratio >= 1.2: return 1.00
    if ratio >= 0.9: return 0.97
    if ratio >= 0.7: return 0.92
    if ratio >= 0.5: return 0.85
    return 0.78

def get_optimal_price(mrp, cost, target_margin, days_remaining, shelf_life, sold_per_day, stock):
    expiry_score = calculate_expiry_score(days_remaining, shelf_life)
    velocity_mult = calculate_velocity_multiplier(sold_per_day, stock, days_remaining)
    min_price = cost * (1 + target_margin / 100)
    max_discount = (expiry_score / 100) * 0.35
    optimal = mrp * (1 - max_discount) * velocity_mult
    final_price = max(round(optimal), math.ceil(min_price))
    actual_margin = round(((final_price - cost) / final_price) * 100, 2)
    return {
        "optimal_price": final_price,
        "expiry_score": expiry_score,
        "velocity_multiplier": round(velocity_mult, 4),
        "min_price": round(min_price, 2),
        "actual_margin": actual_margin,
    }

@app.get("/")
def root():
    return {"message": "FreshDrop Pricing Engine API", "version": "1.0.0", "status": "running"}

@app.get("/products")
def get_products():
    result = []
    for p in PRODUCTS:
        algo = get_optimal_price(p["mrp"], p["cost"], p["targetMargin"],
                                 p["daysRemaining"], p["shelfLife"], p["soldPerDay"], p["stock"])
        trigger = CATEGORY_TRIGGERS.get(p["category"], 3)
        status = "critical" if (p["daysRemaining"] / p["shelfLife"]) <= 0.2 or p["daysRemaining"] <= 2 \
                 else "warning" if (p["daysRemaining"] / p["shelfLife"]) <= 0.4 or p["daysRemaining"] <= 5 \
                 else "safe"
        result.append({**p, **algo, "trigger_days": trigger,
                        "is_triggered": p["daysRemaining"] <= trigger, "status": status})
    return result

@app.post("/optimize")
async def optimize_price(req: OptimizeRequest):
    algo = get_optimal_price(req.mrp, req.cost, req.targetMargin,
                             req.daysRemaining, req.shelfLife, req.soldPerDay, req.stock)
    trigger = CATEGORY_TRIGGERS.get(req.category, 3)
    note_data = {
        "product_id": req.id, "product_name": req.name,
        "old_price": req.mrp, "new_price": algo["optimal_price"],
        "margin": algo["actual_margin"], "expiry_score": algo["expiry_score"],
        "timestamp": int(time.time())
    }
    txid, explorer_url = await algo_service.record_price_update(note_data)
    return {
        "product_id": req.id, "product_name": req.name,
        "old_price": req.mrp, "optimal_price": algo["optimal_price"],
        "margin_pct": algo["actual_margin"], "expiry_score": algo["expiry_score"],
        "velocity_multiplier": algo["velocity_multiplier"],
        "trigger_days": trigger, "is_triggered": req.daysRemaining <= trigger,
        "min_price": algo["min_price"], "txid": txid, "explorer_url": explorer_url,
        "algo_address": algo_service.address, "timestamp": time.time()
    }

@app.get("/wallet")
def get_wallet():
    return {
        "address": algo_service.address,
        "explorer": f"https://testnet.algoexplorer.io/address/{algo_service.address}",
        "faucet": "https://bank.testnet.algorand.network/"
    }

@app.get("/health")
def health():
    return {"status": "ok", "algorand": "testnet", "endpoint": "algonode.cloud"}
