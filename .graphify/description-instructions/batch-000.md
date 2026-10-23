# Node Description Batch 1 of 1

Graphify is running in assistant/skill mode (no API key). You are the host
assistant (Claude Code / Codex / Gemini CLI). Read the prompt below and write
your JSON answer to the answer file.

## Prompt

You are documenting nodes in a knowledge graph.
For each entry below, write ONE concise factual plain-language sentence
describing what it is or does. Use only the provided context.
For a code symbol (kind=code-symbol — a function, class, or constant),
describe what the function/symbol does based on its name, source location
and neighbors — e.g. "Resolves the configured ontology profile from graphify.yaml.".
For an entity node (any other kind — e.g. a person, place, event, object),
describe what the entity is and its role, grounded in its type, its
relations (neighbors) and the provided citations/evidence — e.g.
"Lady Carfax, a wealthy heiress who disappears en route to Lausanne.".
Ground entity descriptions in the citations/evidence when present; do not
speculate beyond the context, so a node with no supporting context may be
left out of the reply.
Write every description in English (en). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "loan_calc_calculator": "calculator.py" | kind=code-symbol | source=loan_calc/calculator.py:L1 | neighbors=[amortisation_schedule(), compare_offers(), eligible_amount(), emi(), format_inr(), _monthly_rate()]
- "loan_calc_calculator_emi": "emi()" | kind=code-symbol | source=loan_calc/calculator.py:L13 | neighbors=[calculator.py, amortisation_schedule(), compare_offers(), _monthly_rate(), prepayment_savings(), summary()]
- "loan_calc_calculator_prepayment_savings": "prepayment_savings()" | kind=code-symbol | source=loan_calc/calculator.py:L78 | neighbors=[calculator.py, amortisation_schedule(), emi(), remaining_tenure(), total_interest(), Keep the same EMI after a lump-sum prep…]
- "loan_calc_calculator_amortisation_schedule": "amortisation_schedule()" | kind=code-symbol | source=loan_calc/calculator.py:L33 | neighbors=[calculator.py, emi(), _monthly_rate(), outstanding_after(), prepayment_savings()]
- "loan_calc_calculator_summary": "summary()" | kind=code-symbol | source=loan_calc/calculator.py:L153 | neighbors=[calculator.py, emi(), format_inr(), total_interest(), total_payment()]
- "loan_calc_calculator_total_interest": "total_interest()" | kind=code-symbol | source=loan_calc/calculator.py:L29 | neighbors=[calculator.py, compare_offers(), prepayment_savings(), summary(), total_payment()]
- "loan_calc_calculator_monthly_rate": "_monthly_rate()" | kind=code-symbol | source=loan_calc/calculator.py:L8 | neighbors=[calculator.py, amortisation_schedule(), eligible_amount(), emi()]
- "loan_calc_calculator_total_payment": "total_payment()" | kind=code-symbol | source=loan_calc/calculator.py:L25 | neighbors=[calculator.py, summary(), total_interest(), emi()]
- "loan_calc_calculator_compare_offers": "compare_offers()" | kind=code-symbol | source=loan_calc/calculator.py:L102 | neighbors=[calculator.py, emi(), total_interest()]
- "loan_calc_calculator_eligible_amount": "eligible_amount()" | kind=code-symbol | source=loan_calc/calculator.py:L119 | neighbors=[calculator.py, _monthly_rate()]
- "loan_calc_calculator_format_inr": "format_inr()" | kind=code-symbol | source=loan_calc/calculator.py:L130 | neighbors=[calculator.py, summary()]
- "loan_calc_calculator_outstanding_after": "outstanding_after()" | kind=code-symbol | source=loan_calc/calculator.py:L57 | neighbors=[calculator.py, amortisation_schedule()]
- "loan_calc_calculator_remaining_tenure": "remaining_tenure()" | kind=code-symbol | source=loan_calc/calculator.py:L66 | neighbors=[calculator.py, prepayment_savings()]
- "cli": "cli.py" | kind=code-symbol | source=cli.py:L1 | neighbors=[main()]
- "cli_main": "main()" | kind=code-symbol | source=cli.py:L7 | neighbors=[cli.py]
- "loan_calc_calculator_rationale_79": "Keep the same EMI after a lump-sum prepayment and shorten the tenure." | kind=entity | source=loan_calc/calculator.py:L79 | neighbors=[prepayment_savings()]
- "loan_calc_calculator_schedule_to_csv": "schedule_to_csv()" | kind=code-symbol | source=loan_calc/calculator.py:L146 | neighbors=[calculator.py]
- "loan_calc_init": "__init__.py" | kind=code-symbol | source=loan_calc/__init__.py:L1

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\Users\ziyang.tan\OneDrive - NTT Ltd\Desktop\loan-calc\loan-calc\.graphify\description-instructions\batch-000.json

Keep each description factual and concise (one sentence). No markdown, no prose
outside the JSON object. It is acceptable to omit a node if context is
insufficient — but include every node you can ground confidently.

Example answer format:
```json
{
  "node_id_1": "Resolves the configured ontology profile from graphify.yaml.",
  "node_id_2": "Colonel James Barclay, an antagonist in The Crooked Man."
}
```
