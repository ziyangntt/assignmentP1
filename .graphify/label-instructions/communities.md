# Community Labeling

Graphify is running in assistant/skill mode (no API key). You are the host
assistant (Claude Code / Codex / Gemini CLI). Read the community listing below
and write 2-5 word plain-language names for each.

## Language

Write every name in English (en). Do not switch languages.

## Communities

Community 0: amortisation_schedule(, _monthly_rate(, outstanding_after(, calculator.py, eligible_amount(, format_inr(, schedule_to_csv(
Community 1: compare_offers(, emi(, summary(, total_interest(, total_payment(
Community 2: prepayment_savings(, remaining_tenure(, Keep the same EMI after a lump-sum prepayment and shorten th
Community 3: cli.py, main(
Community 4: __init__.py

## Instructions

Write a single JSON object mapping each community id (as a string) to its
2-5 word name to: c:\Users\ziyang.tan\OneDrive - NTT Ltd\Desktop\loan-calc\loan-calc\.graphify\label-instructions\communities.json

Example:
```json
{
  "0": "Authentication Flow",
  "1": "Authentication Flow",
  "2": "Authentication Flow"
}
```

Then re-run `graphify update` (or `graphify label`) to ingest the names.
