import express from "express"
import { logger } from "./logger"
import Ajv from "ajv"
import addFormats from 'ajv-formats'
import jsonSchema from './FraudScore.json'
import { FraudAnalysisInput, normalizar } from "./normalizacao"
import { history } from "./history"

const app = express()
app.use(express.json())
app.disable('x-powered-by')

app.get("/ready", (_req, res) => {
    logger.info("Rota /ready");
    res.status(200).end()
})

const ajv = new Ajv({ allErrors: true, messages: false })
addFormats(ajv)
const validate = ajv.compile(jsonSchema)

app.post("/fraud-score", (request, res) => {
    logger.info({ request: request.body }, "Recebendo request para analise de fraude");

    if (!validate(request.body)) {
      logger.info({ validacao: ajv.errorsText(validate.errors) }, "Falha na validacao dos dados")
      return res.status(400).json({ error: "Validation Error", details: ajv.errorsText(validate.errors) })
    }

    const transacoesAnalisadas = 5
    const query = normalizar(request.body as FraudAnalysisInput)
    const similares = history(query, transacoesAnalisadas)
    const fraud_score = similares.filter(tx => tx.label === 'fraud').length / transacoesAnalisadas
    const approved = fraud_score < 0.6

    res.json({ approved, fraud_score })
})

const PORT = process.env.PORT ?? 3000
app.listen(PORT, () => {
    logger.info(`Server running on http://localhost:${PORT}`)
})