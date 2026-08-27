-- Metric View: mv_customer_risk
-- Source: gold_customer_position
-- Consumers: dashboard KPI tiles, Genie headline answers, app KPI cards

USE SCHEMA meridian_bank;

CREATE OR REPLACE VIEW mv_customer_risk WITH METRICS LANGUAGE YAML AS
$$
version: 1.1
comment: "Customer risk metric view for Meridian Bank retention dashboard"
source: oh_phi_workspace.meridian_bank.gold_customer_position
fields:
- name: tier
  expr: tier
- name: risk_band
  expr: risk_band
- name: home_metro
  expr: home_metro
measures:
- name: balance_at_risk
  expr: SUM(balance_at_risk_usd)
- name: revenue_at_risk
  expr: SUM(revenue_at_risk_usd)
- name: total_balance
  expr: SUM(total_balance_usd)
- name: customer_count
  expr: COUNT(1)
- name: critical_count
  expr: SUM(CASE WHEN risk_band = 'critical' THEN 1 ELSE 0 END)
- name: elevated_count
  expr: SUM(CASE WHEN risk_band = 'elevated' THEN 1 ELSE 0 END)
- name: atrisk_count
  expr: SUM(CASE WHEN risk_band IN ('critical','elevated') THEN 1 ELSE 0 END)
- name: avg_attrition_risk
  expr: AVG(attrition_risk_score)
- name: avg_churn_signal
  expr: AVG(churn_signal_score)
$$;
