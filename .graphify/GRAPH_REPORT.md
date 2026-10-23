# Graph Report - .  (2026-10-23)

## Corpus Check
- Corpus is ~660 words - fits in a single context window. You may not need a graph.

## Summary
- 18 nodes · 32 edges · 3 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output
- Edge kinds: calls: 17 · contains: 14 · rationale_for: 1


## Input Scope
- Requested: all
- Resolved: all (source: configured-default)
- Included files: 3 · Candidates: recursive
- Excluded: 0 untracked · 0 ignored · 0 sensitive · 0 missing committed
## God Nodes (most connected - your core abstractions)
1. `emi()` - 7 edges
2. `prepayment_savings()` - 6 edges
3. `total_interest()` - 5 edges
4. `amortisation_schedule()` - 5 edges
5. `summary()` - 5 edges
6. `_monthly_rate()` - 4 edges
7. `total_payment()` - 4 edges
8. `compare_offers()` - 3 edges
9. `outstanding_after()` - 2 edges
10. `remaining_tenure()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `amortisation_schedule()` --calls--> `emi()`  [EXTRACTED]
  loan_calc/calculator.py → loan_calc/calculator.py  _Bridges community 0 → community 1_
- `prepayment_savings()` --calls--> `amortisation_schedule()`  [EXTRACTED]
  loan_calc/calculator.py → loan_calc/calculator.py  _Bridges community 2 → community 0_
- `prepayment_savings()` --calls--> `emi()`  [EXTRACTED]
  loan_calc/calculator.py → loan_calc/calculator.py  _Bridges community 2 → community 1_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.43
Nodes (5): amortisation_schedule(), eligible_amount(), format_inr(), _monthly_rate(), outstanding_after()

### Community 1 - "Community 1"
Cohesion: 0.70
Nodes (5): compare_offers(), emi(), summary(), total_interest(), total_payment()

### Community 2 - "Community 2"
Cohesion: 0.67
Nodes (3): prepayment_savings(), Keep the same EMI after a lump-sum prepayment and shorten the tenure., remaining_tenure()

## Knowledge Gaps
- **1 isolated node(s):** `Keep the same EMI after a lump-sum prepayment and shorten the tenure.`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `prepayment_savings()` connect `Community 2` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `emi()` connect `Community 1` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `total_interest()` connect `Community 1` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `Keep the same EMI after a lump-sum prepayment and shorten the tenure.` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._