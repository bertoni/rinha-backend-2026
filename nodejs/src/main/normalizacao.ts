export type FraudAnalysisInput = {
    id: string
    transaction: {
        amount: number
        installments: number
        requested_at: string
    }
    customer: {
        avg_amount: number
        tx_count_24h: number
        known_merchants: string[]
    }
    merchant: {
        id: string
        mcc: string
        avg_amount: number
    }
    terminal: {
        is_online: boolean
        card_present: boolean
        km_from_home: number
    }
    last_transaction?: {
        timestamp: string
        km_from_current: number
    }
}

const limitar = (valor: number, limite: number): number => {
    const normalizado = limite ? valor / limite : 0
    return normalizado < 0 ? 0 : normalizado > 1 ? 1 : normalizado
}

const diffInMinutes = (a: Date, b: Date): number => {
  const diffMs = a.getTime() - b.getTime()
  return diffMs / (1000 * 60)
}

const limites = {
  max_amount: 10000,
  max_installments: 12,
  amount_vs_avg_ratio: 10,
  max_minutes: 1440,
  max_km: 1000,
  max_tx_count_24h: 20,
  max_merchant_avg_amount: 10000
}

const mcc_risk_table: Record<string, number> = {
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

export const normalizar = (input: FraudAnalysisInput): number[] => {
    const normalizados: number[] = []
    const requested_at = new Date(input.transaction.requested_at)

    const amount = limitar(input.transaction.amount, limites.max_amount)
    normalizados.push(amount)

    const installments = limitar(input.transaction.installments, limites.max_installments)
    normalizados.push(installments)
    
    const amount_vs_avg = limitar(limitar(input.transaction.amount, input.customer.avg_amount), limites.amount_vs_avg_ratio)
    normalizados.push(amount_vs_avg)
    
    const hour_of_day = limitar(requested_at.getHours(), 23)
    normalizados.push(hour_of_day)

    const day_of_week = limitar(requested_at.getUTCDay(), 6)
    normalizados.push(day_of_week)
    
    const minutes_since_last_tx = input.last_transaction
        ? limitar(Math.floor(diffInMinutes(requested_at, new Date(input.last_transaction.timestamp))), limites.max_minutes)
        : -1
    normalizados.push(minutes_since_last_tx)

    const km_from_last_tx = input.last_transaction ? limitar(input.last_transaction.km_from_current, limites.max_km) : -1
    normalizados.push(km_from_last_tx)

    const km_from_home = limitar(input.terminal.km_from_home, limites.max_km)
    normalizados.push(km_from_home)
    
    const tx_count_24h = limitar(input.customer.tx_count_24h, limites.max_tx_count_24h)
    normalizados.push(tx_count_24h)
    
    const is_online = input.terminal.is_online ? 1 : 0
    normalizados.push(is_online)
    
    const card_present = input.terminal.card_present ? 1 : 0
    normalizados.push(card_present)
    
    const unknown_merchant = !input.customer.known_merchants.includes(input.merchant.id) ? 1 : 0
    normalizados.push(unknown_merchant)
    
    const mcc_risk = mcc_risk_table[input.merchant.mcc] ?? 0.5
    normalizados.push(mcc_risk)
    
    const merchant_avg_amount = limitar(input.merchant.avg_amount, limites.max_merchant_avg_amount)
    normalizados.push(merchant_avg_amount)

    return normalizados
}