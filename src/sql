CREATE TABLE IF NOT EXISTS sales (
    order_id       TEXT PRIMARY KEY,
    order_date     DATE NOT NULL,
    customer_id    TEXT NOT NULL,
    product        TEXT NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit_price     NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    total_amount   NUMERIC(14, 2) NOT NULL CHECK (total_amount >= 0),
    loaded_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product);
