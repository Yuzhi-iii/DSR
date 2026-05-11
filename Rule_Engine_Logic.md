
# 6. Rule Engine Logic

## 6.1 Role of the rule engine

The rule engine aggregates requirement-level assessments into a case-level screening decision.

Its purpose is not to issue a final legal judgment.  
Instead, it translates structured requirement-level outcomes into a consistent procedural recommendation for procurement-stage handling.

The rule engine therefore determines:

- overall screening-level risk (`low`, `medium`, `high`)
- recommended procedural path
- a short summary rationale
- key requirement-level drivers
- priority follow-up actions

## 6.2 Inputs to the decision layer

The rule engine operates on the output of the requirement mapping layer.

Its primary inputs are:

- `requirement_id`
- `triggered`
- `status`
- `recommended_action`
- `criticality`

The decision layer does not re-read raw case text.  
It relies on structured requirement-level assessments as its input basis.

## 6.3 Aggregation logic

The current aggregation logic follows a conservative screening design.

### High risk

The overall decision is classified as `high` when:

- at least one **triggered** requirement has  
  - `status = potential_gap`  
  - and `criticality = critical`

In such cases, the recommended path is:

- `legal_or_dpo_review`

The rationale is that at least one critical requirement indicates a potentially serious compliance or governance concern that should not be resolved through routine screening alone.

### Medium risk

The overall decision is classified as `medium` when:

- no critical potential gap is present, but
- at least one **important** requirement has `status = potential_gap`, or
- at least one **critical** requirement has `status = insufficient_information`

In such cases, the recommended path is:

- `officer_review`

The rationale is that the case cannot be cleared confidently, but does not yet show a critical potential gap that automatically requires legal or DPO escalation.
This category excludes cases where the only unresolved issues are `insufficient_information` findings limited to `MR2`, `MR5`, and `MR8`, as those are treated as a lower-risk clarification scenario.

### Low risk

The overall decision is classified as `low` in either of the following situations.

#### Low risk with direct progression

The overall decision is classified as `low` when:

- all requirements are either  
  - `met`, or  
  - `not_triggered`

In such cases, the recommended path is:

- `accept_and_proceed`

The rationale is that the screening results do not indicate unresolved concerns that require additional clarification before routine progression.

#### Low risk with information follow-up

The overall decision is also classified as `low` when:

- no triggered requirement has `status = potential_gap`, and
- all requirement-level results are within  
  - `met`,  
  - `not_triggered`, or  
  - `insufficient_information`, and
- any `insufficient_information` result is limited to the following lower-impact governance or documentation requirements:  
  - `MR2`  
  - `MR5`  
  - `MR8`

In such cases, the recommended path is:

- `request_more_information`

The rationale is that the case does not show substantive screening red flags, but some governance or documentation details remain incomplete and should be clarified before progression.


### Fallback rule

If the combination of requirement-level results does not fit the rules above, the system assigns:

- `overall_risk = medium`
- `recommended_path = officer_review`

This fallback preserves conservative manual review where the signal mix is ambiguous.

## 6.4 Output construction


### Summary rationale

The `summary_rationale` field provides a short explanation of why the overall decision was assigned.

It is generated from the dominant rule condition, for example:

- “At least one critical requirement has a potential gap.”
- “There are non-trivial gaps or insufficient information affecting reliable screening.”
- “All assessed requirements are met or not triggered.”
- “The case does not show substantive screening red flags, but some governance and documentation details remain incomplete.”

### Key drivers

The `key_drivers` field identifies the most important requirement-level contributors to the overall result.

These are represented in compact form, such as:

- `MR1 potential_gap`
- `MR5 potential_gap`
- `MR7 potential_gap`

Key drivers are selected from the highest-priority triggered requirements relevant to the aggregation outcome.

### Priority actions

The `priority_actions` field translates the main requirement-level concerns into business-oriented next steps.

Examples include:

- Clarify legal basis and Article 9 condition.
- Clarify processing purpose, deployment context, and actor roles.
- Provide fuller vendor documentation for screening.
- Clarify controller, processor, and possible joint-controller roles.
- Clarify hosting, storage, and transfer/access arrangements.
- Describe meaningful human oversight arrangements.

These actions are not final legal instructions.  
They are screening-stage recommendations that help route the case toward the next appropriate step.

## 6.5 Interpretive boundary

The rule engine produces a screening decision, not a definitive legal determination.

For example:

- `high` risk does not mean the procurement is unlawful
- `medium` risk does not mean the case is acceptable
- `low` risk does not mean full compliance is guaranteed

Instead, the output should be interpreted as a structured procedural recommendation based on the currently available evidence and requirement-level assessments.

This boundary is important because the system is designed as a decision-support artifact, not as an autonomous legal decision-maker.