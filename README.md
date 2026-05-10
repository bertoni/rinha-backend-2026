# Rinha Backend 2026 - Fraud Detection

Aplicação usando Python + Nginx

## Rodando localmente

Dentro da pasta `python/` inicialmente criar o ambiente virtual:
```
pyenv install 3.13.0
pyenv local 3.13.0
python -m venv .venv
source .venv/bin/activate
```

Devemos dentro do ambiente virtual criado e ativado fazer a instalação das dependências:
```
pip install -r requirements.txt
```

Antes de subir a API, precisa se processar o dataset (isso vai gerar 2 arquivos: `index.faiss` e `labels.bin`):
```
python build_index.py
```

Com isso, a API esta disponível para ser executada:
```
make dev
```

A API irá subir na porta 8080


## Subindo toda a stack

Para subir a stack toda com docker, basta usar:
```
docker compose up
```


## Rodar os testes localmente

Usando o mesmo k6, para rodar os testes locais:
```
cd k6/
docker run --rm -i -u $(id -u) -v $PWD:/app -w /app  --network="host" grafana/k6 run - <test.js
```


## Versões e métricas

| Versão | Score    | p99       | TP (True Positive) | TN (True Negative) | FP (False Positive) | FN (False Negative) | Failure Rate | Obs |
| :---   | :---     | :---      | :---               | :---               | :---                | :---                | :---         | :--- |
| 1      | -6000    | 2002.11ms | 4749               | 6933               | 120                 | 839                 | 32.16%       | Modelo em HTTP com IVFPQ (nlist=16, m=2, bits=8, nprobe=16) |
| 2      | -3552.83 | 2001.76ms | 22309              | 28683              | 358                 | 958                 | 5.55%        | Modelo em Socket com IVF Scalar (nlist=4096, bits=8, nprobe=16) |
| 3      | 1228.46  | 68.75ms   | 22833              | 29743              | 279                 | 1204                | 2.74%        | Modelo em Socket com IVF Scalar (nlist=8192, bits=8, nprobe=32), utilização de orjson e otimizações do nginx |
| 4      |          |           |                    |                    |                     |                     |          | Modelo em Socket com IVF Scalar (nlist=8192, bits=8, nprobe=32), remoção do pydantic |
