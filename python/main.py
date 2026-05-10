import orjson
import numpy as np
import faiss
import falcon.asgi
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
    index.nprobe = 32
    
    # Opção com HNSW
    # index.hnsw.efSearch = 32

    ids = np.fromfile(
        "labels.bin",
        dtype=np.uint8
    )

    return index, ids

index, ids = load_data()

class HealthResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_204

def clamp(value: float, limit: float) -> float:
    normalized = (value / limit) if limit > 0 else 0
    return 0 if normalized < 0 else 1 if normalized > 1 else normalized

class PredictResource:
    async def on_post(self, req, resp):
        try:
            raw = await req.stream.read()
            data = orjson.loads(raw)

            transaction = data["transaction"]
            customer = data["customer"]
            merchant = data["merchant"]
            terminal = data["terminal"]
            last_tx = data["last_transaction"]
            
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

            transaction_amount = max(0.0, min(transaction["amount"], 1e6))
            transaction_installments = max(1, min(transaction["installments"], 12))
            transaction_requested_at = datetime.fromisoformat(transaction["requested_at"].replace("Z", "+00:00"))
            customer_avg_amount = max(0.0, min(customer["avg_amount"], 1e6))
            customer_tx_count_24h = max(0, min(customer["tx_count_24h"], 23))
            customer_known_merchants = [] if not isinstance(customer["known_merchants"], list) else customer["known_merchants"]
            merchant_id = '' if not isinstance(merchant["id"], str) or len(merchant["id"]) == 0 else merchant["id"]
            merchant_mcc = '' if not isinstance(merchant["mcc"], str) or len(merchant["mcc"]) == 0 else merchant["mcc"]
            merchant_avg_amount = max(0.0, min(merchant["avg_amount"], 1e6))
            terminal_is_online = terminal["is_online"]
            terminal_card_present = terminal["card_present"]
            terminal_km_from_home = max(0.0, min(terminal["km_from_home"], 1e6))
            
            vec = np.empty(14, dtype=np.float32)
            vec[0] = clamp(transaction_amount, 10000)
            vec[1] = clamp(transaction_installments, 12)
            vec[2] = clamp(clamp(transaction_amount, customer_avg_amount), 10)
            vec[3] = clamp(transaction_requested_at.hour, 23)
            vec[4] = clamp(transaction_requested_at.weekday(), 6)
            vec[5] = clamp((transaction_requested_at - datetime.fromisoformat(last_tx["timestamp"].replace("Z", "+00:00"))).total_seconds() / 60, 1440) if last_tx is not None else -1
            vec[6] = clamp(last_tx["km_from_current"], 1000) if last_tx is not None else -1
            vec[7] = clamp(terminal_km_from_home, 1000)
            vec[8] = clamp(customer_tx_count_24h, 20)
            vec[9] = 1 if terminal_is_online else 0
            vec[10] = 1 if terminal_card_present else 0
            vec[11] = 0 if merchant_id in customer_known_merchants else 1
            vec[12] = mcc_risk_table.get(merchant_mcc) if mcc_risk_table.get(merchant_mcc) is not None else 0.5
            vec[13] = clamp(merchant_avg_amount, 10000)

            transactions_history: int = 5
            faiss.omp_set_num_threads(1)
            query = np.ascontiguousarray(vec.reshape(1, -1), dtype=np.float32)
            faiss.normalize_L2(query)

            distances, indices = index.search(query, transactions_history)

            results = []
            for i, idx in enumerate(indices[0]):
                results.append('fraud' if ids[idx] == 1 else 'legit')

            fraud_score = results.count('fraud') / transactions_history
            approved = fraud_score < 0.6

            resp.content_type = "application/json"
            resp.status = falcon.HTTP_200
            resp.data = orjson.dumps({
                "approved": approved,
                "fraud_score": fraud_score,
            })
        except Exception as e:
            resp.content_type = "application/json"
            resp.status = falcon.HTTP_500
            resp.media = orjson.dumps({
                "error": str(e),
            })


app.add_route("/ready", HealthResource())
app.add_route("/fraud-score", PredictResource())

