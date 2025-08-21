Slide 1 — Goal & Context

Goal: Classify survey comments into one label from a fixed list with privacy, cost controls, and a two-tier LLM cascade.
Stack: Tachyon → Small LLM (Flash/Haiku) → Big LLM (Pro/Sonnet). No model training.

⸻

Slide 2 — Labels & Short Descriptions
	•	billing.refunds — Charged and wants money back or reversal.
	•	billing.chargeback — Bank/card network dispute (chargeback process).
	•	payments.tap_to_pay — Contactless tap fails at terminal/device.
	•	support.rude_agent — Agent rude or unhelpful.
	•	product.defect — Item broken or malfunctioning.

⸻

Slide 3 — Strict JSON Contracts

Small LLM QuickPick (per call): { "label_id": "…", "confidence_pct": 0–100, "taxonomy_version": "v1.12" }
Does‑It‑Fit (per label): { "label_id": "…", "fits": "yes|no", "taxonomy_version": "v1.12" }
Final Result: { "label_id": "…", "reason": "<=2 sentences", "taxonomy_version": "v1.12" }
Big LLM Corrector: { "final_label": "…", "action": "keep|replace", "reason": "<=2 sentences", "taxonomy_version": "v1.12" }

⸻

Slide 4 — Privacy (Pseudonymization)
	•	Detect PII (names, emails, phones, addresses, account/order IDs).
	•	Replace with deterministic tokens using HMAC(key, domain||value) → first 8 hex chars.
	•	Keep pseudonymization_version, domain; mapping stored in vault/KMS.
	•	Block low-confidence PII detections from leaving the trusted boundary.

⸻

Slide 5 — Cost Controls
	•	Compression: Keep 1–2 sentences most relevant to label cues; target 50–70% token cut.
	•	Strict JSON: Validate & locally repair tiny syntax (no re-ask). Reject unknown labels.
	•	Budget Policy: When >80% tokens used today, tighten thresholds or abstain with top‑2 labels.
	•	Caching: Exact & near-duplicate caches. Batch requests when possible.

⸻

Slide 6 — Parallel Small‑LLM Stage
	1.	QuickPick x2 (parallel): ask for label + confidence.
	2.	If (same label & both high confidence) → accept.
	3.	Else → Does‑It‑Fit yes/no for the two labels returned.
	4.	If unambiguous → accept; else → escalate to Big LLM Corrector.

⸻

Slide 7 — Prompts (Short)

QuickPick: “Pick exactly one label_id from list. Return JSON {label_id, confidence_pct, taxonomy_version}.”
Does‑It‑Fit: “Does comment match label:desc? Return JSON {label_id, fits, taxonomy_version} with fits yes|no.”
Corrector: “Given comment + proposed label, choose one allowed label. Return JSON {final_label, action, reason, taxonomy_version}.”

⸻

Slide 8 — Router Thresholds (Defaults)
	•	High confidence = confidence_pct ≥ 75.
	•	Accept if: (QuickPick agree) AND (both ≥75) AND length ≤300 AND compression ≥0.4.
	•	Otherwise run Does‑It‑Fit on both labels; accept if exactly one is yes.
	•	If still ambiguous or budget tight → Big LLM Corrector (one call).

⸻

Slide 9 — Example A (Refund) ⇒ Small LLM Accepts

Comment: “Double‑charged, still no refund.”
QuickPick: both billing.refunds @ 90/85 ⇒ accept.

⸻

Slide 10 — Example B (Refund vs Chargeback) ⇒ Escalate

Comment: “Bank opened dispute due to no refund.”
QuickPick: refunds@70, chargeback@78 (disagree/high). Does‑It‑Fit: refunds=no, chargeback=yes ⇒ accept chargeback or confirm with Big LLM if policy requires.

⸻

Slide 11 — Example C (Tap‑to‑Pay + PII)

PII → tokens; compress long text.
QuickPick both payments.tap_to_pay @ 82/88 ⇒ accept. If compression <0.4 & budget tight ⇒ abstain or escalate per policy.

⸻

Slide 12 — Metrics Dashboard
	•	Tokens/req, $/1k comments, latency p95, escalation rate.
	•	JSON failure/repair rate, compression ratio, PII replacements.
	•	Agreement rate (QuickPick), Does‑It‑Fit outcomes.

⸻

Slide 13 — Rollout Plan (2 weeks)
	•	Week 1: Pseudonymize + compression + QuickPick.
	•	Week 2: Add Does‑It‑Fit and Corrector; turn on budget policy & caching.

⸻

Slide 14 — One‑Line Claim

“Privacy‑preserving, budget‑aware two‑tier LLM cascade with parallel small‑LLM voting and label‑fit verification producing strict JSON outputs for fixed taxonomy classification.”
