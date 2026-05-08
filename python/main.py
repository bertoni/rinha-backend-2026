import json
import numpy as np
import faiss
import falcon.asgi
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from datetime import datetime
from typing import Optional, List

app = falcon.asgi.App()

# Variáveis globais
index = None
ids = []

def load_data():
    global index, ids

    index = faiss.read_index("index.faiss")
    
    # Opção com IVF Flat
    index.nprobe = 3
    
    # Opção com HNSW
    # index.hnsw.efSearch = 32

    ids = np.fromfile(
        "labels.bin",
        dtype=np.uint8
    )

    return index, ids

index, ids = load_data()


class Transaction(BaseModel):
    amount: float = Field(..., ge=0)
    installments: int = Field(..., ge=1)
    requested_at: datetime

class Customer(BaseModel):
    avg_amount: float = Field(..., ge=0)
    tx_count_24h: int = Field(..., ge=0)
    known_merchants: List[str]

class Merchant(BaseModel):
    id: str = Field(..., min_length=1)
    mcc: str = Field(..., min_length=1)
    avg_amount: float = Field(..., ge=0)

class Terminal(BaseModel):
    is_online: bool
    card_present: bool
    km_from_home: float = Field(..., ge=0)

class LastTransaction(BaseModel):
    timestamp: datetime
    km_from_current: float = Field(..., ge=0)

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(..., min_length=1)
    transaction: Transaction
    customer: Customer
    merchant: Merchant
    terminal: Terminal
    last_transaction: Optional[LastTransaction] = None

    def limit(self, value: float, limit: float) -> float:
        normalized = (value / limit) if limit > 0 else 0
        return 0 if normalized < 0 else 1 if normalized > 1 else normalized

    def normalization(self) -> List[float]:
        data: List[float] = []

        max_amount = 10000
        max_installments = 12
        amount_vs_avg_ratio = 10
        max_minutes = 1440
        max_km = 1000
        max_tx_count_24h = 20
        max_merchant_avg_amount = 10000
        mcc_risk_table: dict[str, float] = {
            "5411": 0.15,
            "5812": 0.30,
            "5912": 0.20,
            "5944": 0.45,
            "7801": 0.80,
            "7802": 0.75,
            "7995": 0.85,
            "4511": 0.35,
            "5311": 0.25,
            "5999": 0.50,
        }

        amount = self.limit(self.transaction.amount, max_amount)
        data.append(amount)

        installments = self.limit(self.transaction.installments, max_installments)
        data.append(installments)

        amount_vs_avg = self.limit(self.limit(self.transaction.amount, self.customer.avg_amount), amount_vs_avg_ratio)
        data.append(amount_vs_avg)

        hour_of_day = self.limit(self.transaction.requested_at.hour, 23)
        data.append(hour_of_day)

        day_of_week = self.limit(self.transaction.requested_at.weekday(), 6)
        data.append(day_of_week)

        minutes_since_last_tx = self.limit((self.transaction.requested_at - self.last_transaction.timestamp).total_seconds() / 60, max_minutes) if self.last_transaction is not None else -1
        data.append(minutes_since_last_tx)

        km_from_last_tx = self.limit(self.last_transaction.km_from_current, max_km) if self.last_transaction is not None else -1
        data.append(km_from_last_tx)

        km_from_home = self.limit(self.terminal.km_from_home, max_km)
        data.append(km_from_home)

        tx_count_24h = self.limit(self.customer.tx_count_24h, max_tx_count_24h)
        data.append(tx_count_24h)

        is_online = 1 if self.terminal.is_online else 0
        data.append(is_online)

        card_present = 1 if self.terminal.card_present else 0
        data.append(card_present)

        unknown_merchant = 0 if self.merchant.id in self.customer.known_merchants else 1
        data.append(unknown_merchant)

        mcc_risk = mcc_risk_table.get(self.merchant.mcc) if mcc_risk_table.get(self.merchant.mcc) is not None else 0.5
        data.append(mcc_risk)

        merchant_avg_amount = self.limit(self.merchant.avg_amount, max_merchant_avg_amount)
        data.append(merchant_avg_amount)

        return data


class HealthResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_204

class PredictResource:
    async def on_post(self, req, resp):
        try:
            body = await req.get_media()

            payload = PredictRequest(**body)

            transactions_history: int = 5
            query = np.array([payload.normalization()]).astype("float32")
            faiss.normalize_L2(query)

            distances, indices = index.search(query, transactions_history)

            results = []
            for i, idx in enumerate(indices[0]):
                results.append('fraud' if ids[idx] == 1 else 'legit')

            fraud_score = results.count('fraud') / transactions_history
            approved = fraud_score < 0.6

            resp.media = {
                "approved": approved,
                "fraud_score": fraud_score,
            }
        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {
                "errors": e.errors()
            }
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {
                "error": str(e)
            }


app.add_route("/ready", HealthResource())
app.add_route("/fraud-score", PredictResource())

