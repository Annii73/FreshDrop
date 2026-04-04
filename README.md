# FreshDrop — Margin-Aware Pricing Engine
### Hacknovate 7.0 · Code Squad

A **revenue management system for quick commerce perishables** that:
- Calculates optimal prices using expiry timeline + sales velocity
- Guards your target margin (never panic-sells)
- Logs every price update as a **real Algorand Testnet transaction**
- Shows blockchain proof via Lora (AlgoKit Explorer)

---

## 🌐 Live Demo

- **Frontend:** https://annii73.github.io/FreshDrop/frontend/
- **Backend API:** https://freshdrop-f6zi.onrender.com
- **Blockchain Explorer:** https://lora.algokit.io/testnet

---

## 📁 Project Structure

```
freshdrop/
├── backend/
│   ├── main.py                # FastAPI app + pricing algorithm
│   ├── algorand_service.py    # Algorand SDK integration
│   ├── requirements.txt
│   └── algo_wallet.json       # Auto-generated on first run
└── frontend/
    └── index.html             # Complete single-file frontend
```

---

## ⚡ Quick Start

### Step 1 — Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2 — Start the backend

```bash
uvicorn main:app --reload --port 8000
```

On first run you'll see:
```
[Algorand] NEW wallet created: ABCDEF...XYZ
[Algorand] Fund it at: https://lora.algokit.io/testnet
```

### Step 3 — Fund the Algorand wallet

1. Copy the wallet address printed in the terminal
2. Go to https://lora.algokit.io/testnet → Fund section
3. Paste the address and request test ALGO (takes ~10 seconds)

Or run:
```bash
curl http://localhost:8000/wallet
```
and use the faucet URL returned.

### Step 4 — Open the frontend

Simply open `frontend/index.html` in any browser.
The frontend auto-connects to `http://localhost:8000`.

---

## 🔑 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Health check |
| GET | `/products` | All products with pricing |
| POST | `/optimize` | Optimize price + log on Algorand |
| GET | `/wallet` | Wallet address + explorer links |
| GET | `/health` | Backend/Algorand status |

### POST /optimize — Example

```json
{
  "id": 2,
  "name": "Cold Press Orange Juice",
  "category": "Fresh Juice",
  "mrp": 90,
  "cost": 52,
  "targetMargin": 25,
  "stock": 45,
  "soldPerDay": 12,
  "shelfLife": 7,
  "daysRemaining": 2
}
```

### Response

```json
{
  "product_id": 2,
  "product_name": "Cold Press Orange Juice",
  "old_price": 90,
  "optimal_price": 72,
  "margin_pct": 27.8,
  "expiry_score": 71.0,
  "velocity_multiplier": 0.92,
  "trigger_days": 2,
  "is_triggered": true,
  "min_price": 65.0,
  "txid": "ALGO_TXID_HERE",
  "explorer_url": "https://lora.algokit.io/testnet/transaction/ALGO_TXID_HERE",
  "algo_address": "YOUR_WALLET",
  "timestamp": 1712345678.0
}
```

---

## 🧮 Pricing Algorithm

```
expiryScore       = (1 - daysRemaining / shelfLife) × 100

velocityMult      = f(soldPerDay / (stock / daysRemaining))
                    1.00 if selling 120%+ of required rate
                    0.97 if 90–120%
                    0.92 if 70–90%
                    0.85 if 50–70%
                    0.78 if below 50%

minPrice          = cost × (1 + targetMargin%)

optimalPrice      = MRP × (1 − expiryScore/100 × 0.35) × velocityMult

finalPrice        = max(optimalPrice, minPrice)   ← margin guard
```

### Category Trigger Days
| Category | Trigger Window |
|----------|---------------|
| Dairy | Last 3 days |
| Bakery | Last 2 days |
| Fresh Juice | Last 2 days |
| Ready-to-eat | Last 2 days |
| Healthy Snacks | Last 7 days |
| Regular Snacks | Last 14 days |

---

## ⛓ Algorand Integration

- Uses **py-algorand-sdk** with Algonode public Testnet endpoint (no API key needed)
- Generates a wallet on first run and saves to `algo_wallet.json`
- Each price update = **0 ALGO self-send transaction** with JSON note:

```json
{
  "product_id": 2,
  "product_name": "Cold Press Orange Juice",
  "old_price": 90,
  "new_price": 72,
  "margin": 27.8,
  "expiry_score": 71.0,
  "velocity_mult": 0.92,
  "timestamp": 1712345678
}
```

- Returns real TxID linkable on https://lora.algokit.io/testnet
- Falls back to simulated TxID if wallet is not yet funded (demo still works)

---

## 🚀 Demo Mode (No Backend)

The frontend works standalone — if the backend is offline, it:
- Uses built-in product data
- Runs the pricing algorithm in JavaScript
- Generates a simulated (but formatted-real) TxID
- Still shows full algorithm breakdown + before/after comparison

This means you can open `index.html` directly for a hackathon demo without any setup.

---

## 🏁 Hackathon Checklist

- [x] Product dashboard with status indicators
- [x] Pricing algorithm (expiry score + velocity multiplier + margin guard)
- [x] Category-based trigger system
- [x] Optimize Price button with algorithm breakdown
- [x] Real Algorand Testnet transaction logging
- [x] Blockchain explorer proof link (via Lora AlgoKit)
- [x] Blockchain log panel
- [x] Before vs after revenue comparison
- [x] Total margin saved tracker
- [x] Filter by status (critical / at risk / healthy)
- [x] Optimize All Critical button
- [x] Demo mode (works without backend)
- [x] 12 products across 5 categories
