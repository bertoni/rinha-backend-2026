import test from "node:test"
import assert from "node:assert"
import { normalizar } from "main/normalizacao"

test("Deve retornar valores normalizados sem última transação", () => {
    const input = {
        id: "1234",
        transaction: {
            amount: 500,
            installments: 3,
             requested_at: '2026-05-04T10:15:12.000Z',
        },
        customer: {
            avg_amount: 678,
            tx_count_24h: 2,
            known_merchants: ["MERC-009", "MERC-001", "MERC-001"],
        },
        merchant: {
            id: "MERC-005",
            mcc: "9999999999",
            avg_amount: 399,
        },
        terminal: {
            is_online: false,
            card_present: false,
            km_from_home: 12,
        },
        last_transaction: undefined,
    }

    const dadosNormalizados = normalizar(input)
    assert.strictEqual(dadosNormalizados[0], 0.05)
    assert.strictEqual(dadosNormalizados[1], 0.25)
    assert.strictEqual(dadosNormalizados[2], 0.07374631268436578)
    assert.strictEqual(dadosNormalizados[3], 0.43478260869565216)
    assert.strictEqual(dadosNormalizados[4], 0.16666666666666666)
    assert.strictEqual(dadosNormalizados[5], -1)
    assert.strictEqual(dadosNormalizados[6], -1)
    assert.strictEqual(dadosNormalizados[7], 0.012)
    assert.strictEqual(dadosNormalizados[8], 0.1)
    assert.strictEqual(dadosNormalizados[9], 0)
    assert.strictEqual(dadosNormalizados[10], 0)
    assert.strictEqual(dadosNormalizados[11], 1)
    assert.strictEqual(dadosNormalizados[12], 0.5)
    assert.strictEqual(dadosNormalizados[13], 0.0399)
})

test("Deve retornar valores normalizados com última transação", () => {
    const input = {
        id: "1234",
        transaction: {
            amount: 500,
            installments: 3,
            requested_at: '2026-05-04T10:15:12.000Z',
        },
        customer: {
            avg_amount: 678,
            tx_count_24h: 2,
            known_merchants: ["MERC-009", "MERC-001", "MERC-001"],
        },
        merchant: {
            id: "MERC-005",
            mcc: "9999999999",
            avg_amount: 399,
        },
        terminal: {
            is_online: false,
            card_present: false,
            km_from_home: 12,
        },
        last_transaction: {
            timestamp: '2026-05-04T07:15:12.000Z',
            km_from_current: 20,
        },
    }

    const dadosNormalizados = normalizar(input)
    assert.strictEqual(dadosNormalizados[0], 0.05)
    assert.strictEqual(dadosNormalizados[1], 0.25)
    assert.strictEqual(dadosNormalizados[2], 0.07374631268436578)
    assert.strictEqual(dadosNormalizados[3], 0.43478260869565216)
    assert.strictEqual(dadosNormalizados[4], 0.16666666666666666)
    assert.strictEqual(dadosNormalizados[5], 0.125)
    assert.strictEqual(dadosNormalizados[6], 0.02)
    assert.strictEqual(dadosNormalizados[7], 0.012)
    assert.strictEqual(dadosNormalizados[8], 0.1)
    assert.strictEqual(dadosNormalizados[9], 0)
    assert.strictEqual(dadosNormalizados[10], 0)
    assert.strictEqual(dadosNormalizados[11], 1)
    assert.strictEqual(dadosNormalizados[12], 0.5)
    assert.strictEqual(dadosNormalizados[13], 0.0399)
})