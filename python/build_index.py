import gzip
import json
import numpy as np
import faiss

# -------------------
# LOAD DATA
# -------------------
with gzip.open("./data/references.json.gz", "rt", encoding="utf-8") as f:
    data = json.load(f)

vectors = np.array(
    [item["vector"] for item in data],
    dtype="float32"
)

labels = [item["label"] for item in data]

# -------------------
# (OPCIONAL MAS RECOMENDADO)
# Normalização L2
# -------------------
faiss.normalize_L2(vectors)

dim = vectors.shape[1]

# -------------------
# INDEX (leve e rápido)
# -------------------
# index = faiss.IndexHNSWFlat(dim, 16)  # 16 = mais leve que 32
# index.hnsw.efConstruction = 40        # reduz custo de build

# Opção com IVF Flat
# nlist = 16
# quantizer = faiss.IndexFlatIP(dim)
# index = faiss.IndexIVFFlat(quantizer, dim, nlist)
# index.train(vectors)

# Opção com IVF PQ
# nlist = 4096
# m = 2          # número de subvetores
# bits = 8       # compressão
# quantizer = faiss.IndexFlatIP(dim)
# index = faiss.IndexIVFPQ(quantizer, dim, nlist, m, bits)
# index.train(vectors)

# ---------------------
# Opção com IVF Scalar
dim = 14
nlist = 8192
bits = 8
quantizer = faiss.IndexFlatIP(dim)
index = faiss.IndexIVFScalarQuantizer(quantizer, dim, nlist, bits, faiss.METRIC_INNER_PRODUCT)
vectors = np.ascontiguousarray(
    [item["vector"] for item in data],
    dtype=np.float32
)
faiss.normalize_L2(vectors)
index.train(vectors)
# Opção com IVF Scalar
# ---------------------


index.add(vectors)

# -------------------
# SAVE ARTIFACTS
# -------------------
faiss.write_index(index, "index.faiss")

labels = np.array([
    1 if item["label"] == "fraud" else 0
    for item in data
], dtype=np.uint8)

labels.tofile("labels.bin")

print("Index e labels salvos com sucesso")