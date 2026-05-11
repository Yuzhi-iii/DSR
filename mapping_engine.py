from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


REQUIRED_REQUIREMENT_KEYS = {
    "requirement_id",
    "name",
    "criticality",
    "depends_on",
    "trigger_logic",
    "assessment_rules",
    "default_if_triggered",
    "recommended_action_by_status",
}

ALLOWED_CRITICALITY = {"critical", "important"}

ALLOWED_ASSESSMENT_STATUS = {
    "met",
    "insufficient_information",
    "potential_gap",
}

ALLOWED_RECOMMENDED_ACTIONS = {
    "none",
    "officer_review",
    "proceed_to_next_checks",
    "proceed_with_heightened_checks",
    "request_more_information",
    "request_more_information_or_manual_review",
    "legal_or_dpo_review",
    "accept_and_proceed",
}

ALLOWED_CONDITION_KEYS = {
    "always",
    "all_of",
    "any_of",
    "field",
    "equals",
    "in",
    "not_in",
    "exists",
}

MISSING_SENTINELS = {None, "", "unclear", "not_mentioned", "not_provided"}


@dataclass
class RequirementAssessment:
    requirement_id: str
    name: str
    triggered: bool
    status: str
    rationale: str
    recommended_action: str
    criticality: str
    evidence_refs: Dict[str, str]
    depends_on: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "name": self.name,
            "triggered": self.triggered,
            "status": self.status,
            "rationale": self.rationale,
            "recommended_action": self.recommended_action,
            "criticality": self.criticality,
            "evidence_refs": self.evidence_refs,
            "depends_on": self.depends_on,
        }


def get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def get_value(data: Dict[str, Any], path: str) -> Any:
    return get_nested(data, path, default=None)

def path_exists(data: Dict[str, Any], path: str) -> bool:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    return True


def collect_unknown_value_paths(extraction: Dict[str, Any], requirements: List[Dict[str, Any]]) -> List[str]:
    required_paths = sorted(collect_required_paths(requirements))
    unknown_paths: List[str] = []

    for path in required_paths:
        if not path_exists(extraction, path):
            continue

        value = get_value(extraction, path)

        if value is None or value == "":
            unknown_paths.append(path)
        elif isinstance(value, str) and value in {"unclear", "not_mentioned", "not_provided"}:
            unknown_paths.append(path)

    return unknown_paths

def get_evidence_span(extraction: Dict[str, Any], field_path: str) -> str:
    evidence = extraction.get("evidence_spans", {})
    if not isinstance(evidence, dict):
        return ""

    if field_path in evidence:
        value = evidence[field_path]
        return value if isinstance(value, str) else ""

    key = field_path.split(".")[-1]
    value = evidence.get(key, "")
    return value if isinstance(value, str) else ""


def evaluate_condition(extraction: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    if "always" in condition:
        return bool(condition["always"])
    if "all_of" in condition:
        return all(evaluate_condition(extraction, sub) for sub in condition["all_of"])
    if "any_of" in condition:
        return any(evaluate_condition(extraction, sub) for sub in condition["any_of"])

    field = condition.get("field")
    if not field:
        return False
    value = get_value(extraction, field)

    if "equals" in condition:
        return value == condition["equals"]
    if "in" in condition:
        return value in condition["in"]
    if "not_in" in condition:
        return value not in condition["not_in"]
    if "exists" in condition:
        exists = path_exists(extraction, field)
        return exists == bool(condition["exists"])

    return False


def collect_evidence(extraction: Dict[str, Any], depends_on: List[str]) -> Dict[str, str]:
    refs: Dict[str, str] = {}
    for path in depends_on:
        value = get_value(extraction, path)
        if value is None:
            continue
        refs[path] = get_evidence_span(extraction, path)
    return refs


def validate_condition(condition: Any, where: str) -> None:
    if not isinstance(condition, dict):
        raise ValueError(f"{where} must be an object.")

    unknown_keys = set(condition.keys()) - ALLOWED_CONDITION_KEYS
    if unknown_keys:
        raise ValueError(f"{where} contains unsupported keys: {sorted(unknown_keys)}")

    if "always" in condition:
        if len(condition) != 1:
            raise ValueError(f"{where} with 'always' cannot contain other keys.")
        if not isinstance(condition["always"], bool):
            raise ValueError(f"{where} field 'always' must be a boolean.")
        return

    if "all_of" in condition:
        if len(condition) != 1:
            raise ValueError(f"{where} with 'all_of' cannot contain other keys.")
        if not isinstance(condition["all_of"], list) or not condition["all_of"]:
            raise ValueError(f"{where} field 'all_of' must be a non-empty list.")
        for idx, sub in enumerate(condition["all_of"]):
            validate_condition(sub, f"{where}.all_of[{idx}]")
        return

    if "any_of" in condition:
        if len(condition) != 1:
            raise ValueError(f"{where} with 'any_of' cannot contain other keys.")
        if not isinstance(condition["any_of"], list) or not condition["any_of"]:
            raise ValueError(f"{where} field 'any_of' must be a non-empty list.")
        for idx, sub in enumerate(condition["any_of"]):
            validate_condition(sub, f"{where}.any_of[{idx}]")
        return

    field = condition.get("field")
    if not isinstance(field, str) or not field.strip():
        raise ValueError(f"{where} must contain a non-empty string field 'field'.")

    operators = [op for op in ("equals", "in", "not_in", "exists") if op in condition]
    if len(operators) != 1:
        raise ValueError(
            f"{where} must contain exactly one operator among 'equals', 'in', 'not_in', 'exists'."
        )

    if "in" in condition and (not isinstance(condition["in"], list) or not condition["in"]):
        raise ValueError(f"{where} field 'in' must be a non-empty list.")

    if "not_in" in condition and (
        not isinstance(condition["not_in"], list) or not condition["not_in"]
    ):
        raise ValueError(f"{where} field 'not_in' must be a non-empty list.")

    if "exists" in condition and not isinstance(condition["exists"], bool):
        raise ValueError(f"{where} field 'exists' must be a boolean.")


def collect_condition_fields(condition: Dict[str, Any]) -> Set[str]:
    if "always" in condition:
        return set()
    if "all_of" in condition:
        result: Set[str] = set()
        for sub in condition["all_of"]:
            result.update(collect_condition_fields(sub))
        return result
    if "any_of" in condition:
        result: Set[str] = set()
        for sub in condition["any_of"]:
            result.update(collect_condition_fields(sub))
        return result

    field = condition.get("field")
    return {field} if isinstance(field, str) and field.strip() else set()


def validate_requirements(requirements: List[Dict[str, Any]]) -> None:
    if not isinstance(requirements, list):
        raise ValueError("requirements.json must contain a list of requirement objects.")

    seen_ids: Set[str] = set()

    for i, req in enumerate(requirements):
        if not isinstance(req, dict):
            raise ValueError(f"Requirement at index {i} is not a JSON object.")

        missing = REQUIRED_REQUIREMENT_KEYS - req.keys()
        if missing:
            rid = req.get("requirement_id", f"index {i}")
            raise ValueError(f"Requirement {rid} is missing required keys: {sorted(missing)}")

        rid = req.get("requirement_id", f"index {i}")

        if not isinstance(req.get("requirement_id"), str) or not req["requirement_id"].strip():
            raise ValueError(f"Requirement at index {i} must have a non-empty string 'requirement_id'.")

        if rid in seen_ids:
            raise ValueError(f"Duplicate requirement_id detected: {rid}")
        seen_ids.add(rid)

        if not isinstance(req.get("name"), str) or not req["name"].strip():
            raise ValueError(f"Requirement {rid} must have a non-empty string 'name'.")

        if req.get("criticality") not in ALLOWED_CRITICALITY:
            raise ValueError(
                f"Requirement {rid} has invalid criticality: {req.get('criticality')!r}. "
                f"Allowed values: {sorted(ALLOWED_CRITICALITY)}"
            )

        depends_on = req.get("depends_on")
        if not isinstance(depends_on, list):
            raise ValueError(f"Requirement {rid} field 'depends_on' must be a list.")
        for k, path in enumerate(depends_on):
            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"Requirement {rid} depends_on[{k}] must be a non-empty string.")

        validate_condition(req.get("trigger_logic"), f"Requirement {rid}.trigger_logic")

        assessment_rules = req.get("assessment_rules")
        if not isinstance(assessment_rules, list):
            raise ValueError(f"Requirement {rid} field 'assessment_rules' must be a list.")

        for j, rule in enumerate(assessment_rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Requirement {rid} assessment rule #{j} is not an object.")

            if "if" not in rule or "status" not in rule or "rationale" not in rule:
                raise ValueError(
                    f"Requirement {rid} assessment rule #{j} must contain 'if', 'status', and 'rationale'."
                )

            validate_condition(rule["if"], f"Requirement {rid}.assessment_rules[{j}].if")

            if rule["status"] not in ALLOWED_ASSESSMENT_STATUS:
                raise ValueError(
                    f"Requirement {rid} assessment rule #{j} has invalid status {rule['status']!r}. "
                    f"Allowed values: {sorted(ALLOWED_ASSESSMENT_STATUS)}"
                )

            if not isinstance(rule["rationale"], str) or not rule["rationale"].strip():
                raise ValueError(
                    f"Requirement {rid} assessment rule #{j} must have a non-empty string rationale."
                )

        fallback = req.get("default_if_triggered")
        if not isinstance(fallback, dict):
            raise ValueError(f"Requirement {rid} field 'default_if_triggered' must be an object.")

        if "status" not in fallback or "rationale" not in fallback:
            raise ValueError(
                f"Requirement {rid} default_if_triggered must contain 'status' and 'rationale'."
            )

        if fallback["status"] not in ALLOWED_ASSESSMENT_STATUS:
            raise ValueError(
                f"Requirement {rid} default_if_triggered.status has invalid value {fallback['status']!r}. "
                f"Allowed values: {sorted(ALLOWED_ASSESSMENT_STATUS)}"
            )

        if not isinstance(fallback["rationale"], str) or not fallback["rationale"].strip():
            raise ValueError(
                f"Requirement {rid} default_if_triggered.rationale must be a non-empty string."
            )

        actions = req.get("recommended_action_by_status")
        if not isinstance(actions, dict):
            raise ValueError(
                f"Requirement {rid} field 'recommended_action_by_status' must be an object."
            )

        required_status_keys = {"met", "insufficient_information", "potential_gap"}
        missing_status_keys = required_status_keys - set(actions.keys())
        if missing_status_keys:
            raise ValueError(
                f"Requirement {rid} recommended_action_by_status is missing keys: {sorted(missing_status_keys)}"
            )

        extra_status_keys = set(actions.keys()) - required_status_keys
        if extra_status_keys:
            raise ValueError(
                f"Requirement {rid} recommended_action_by_status has unexpected keys: {sorted(extra_status_keys)}"
            )

        for status_key, action in actions.items():
            if action not in ALLOWED_RECOMMENDED_ACTIONS:
                raise ValueError(
                    f"Requirement {rid} recommended_action_by_status[{status_key!r}] "
                    f"has invalid action {action!r}. Allowed values: {sorted(ALLOWED_RECOMMENDED_ACTIONS)}"
                )


def collect_required_paths(requirements: List[Dict[str, Any]]) -> Set[str]:
    paths: Set[str] = set()
    for req in requirements:
        for path in req.get("depends_on", []):
            paths.add(path)
        trigger_logic = req.get("trigger_logic")
        if isinstance(trigger_logic, dict):
            paths.update(collect_condition_fields(trigger_logic))
        for rule in req.get("assessment_rules", []):
            if isinstance(rule, dict) and isinstance(rule.get("if"), dict):
                paths.update(collect_condition_fields(rule["if"]))
    return paths



def validate_extraction_schema(extraction: Dict[str, Any], requirements: List[Dict[str, Any]]) -> None:
    required_paths = sorted(collect_required_paths(requirements))
    missing_paths = [path for path in required_paths if not path_exists(extraction, path)]
    if missing_paths:
        raise ValueError(
            "Extraction JSON is structurally missing required field paths referenced by requirements: "
            + ", ".join(missing_paths)
        )

class MappingEngine:
    def __init__(self, requirements: List[Dict[str, Any]]):
        validate_requirements(requirements)
        self.requirements = requirements

    @classmethod
    def from_json_file(cls, path: str | Path) -> "MappingEngine":
        with open(path, "r", encoding="utf-8") as f:
            requirements = json.load(f)
        return cls(requirements=requirements)

    def assess_requirement(self, extraction: Dict[str, Any], requirement: Dict[str, Any]) -> RequirementAssessment:
        requirement_id = requirement["requirement_id"]
        name = requirement["name"]
        depends_on = requirement.get("depends_on", [])
        criticality = requirement.get("criticality", "important")

        triggered = evaluate_condition(extraction, requirement.get("trigger_logic", {"always": True}))
        evidence_refs = collect_evidence(extraction, depends_on)

        if not triggered:
            return RequirementAssessment(
                requirement_id=requirement_id,
                name=name,
                triggered=False,
                status="not_triggered",
                rationale="This requirement is not triggered by the extracted case facts.",
                recommended_action="none",
                criticality=criticality,
                evidence_refs=evidence_refs,
                depends_on=depends_on,
            )

        for rule in requirement.get("assessment_rules", []):
            if evaluate_condition(extraction, rule["if"]):
                status = rule["status"]
                recommended_action = requirement.get("recommended_action_by_status", {}).get(
                    status, "officer_review"
                )
                return RequirementAssessment(
                    requirement_id=requirement_id,
                    name=name,
                    triggered=True,
                    status=status,
                    rationale=rule["rationale"],
                    recommended_action=recommended_action,
                    criticality=criticality,
                    evidence_refs=evidence_refs,
                    depends_on=depends_on,
                )

        fallback = requirement.get(
            "default_if_triggered",
            {
                "status": "insufficient_information",
                "rationale": "The requirement was triggered but no rule matched.",
            },
        )
        status = fallback["status"]
        recommended_action = requirement.get("recommended_action_by_status", {}).get(status, "officer_review")
        return RequirementAssessment(
            requirement_id=requirement_id,
            name=name,
            triggered=True,
            status=status,
            rationale=fallback["rationale"],
            recommended_action=recommended_action,
            criticality=criticality,
            evidence_refs=evidence_refs,
            depends_on=depends_on,
        )

    def run(self, extraction: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        validate_extraction_schema(extraction, self.requirements)

        unknown_paths = collect_unknown_value_paths(extraction, self.requirements)
        if unknown_paths:
            print(
                "Warning: extraction contains schema-complete but informationally unresolved fields: "
                + ", ".join(unknown_paths)
            )

        assessments = [self.assess_requirement(extraction, req) for req in self.requirements]
        assessment_dicts = [a.as_dict() for a in assessments]

        mapping_output = {"requirement_assessments": assessment_dicts}
        decision_output = derive_overall_decision(assessment_dicts)
        return mapping_output, decision_output

# Decision layer

def derive_overall_decision(assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
    triggered = [a for a in assessments if a["triggered"]]

    critical_gap_assessments = [
        a for a in triggered if a["status"] == "potential_gap" and a["criticality"] == "critical"
    ]
    important_gap_assessments = [
        a for a in triggered if a["status"] == "potential_gap" and a["criticality"] == "important"
    ]
    critical_insufficient_assessments = [
        a
        for a in triggered
        if a["status"] == "insufficient_information" and a["criticality"] == "critical"
    ]

    def format_driver(a: Dict[str, Any]) -> str:
        return f'{a["requirement_id"]} {a["status"]}'

    def dedupe_keep_order(items: List[str]) -> List[str]:
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def build_priority_actions(selected: List[Dict[str, Any]]) -> List[str]:
        action_map = {
            "MR1": "Clarify legal basis and Article 9 condition.",
            "MR2": "Clarify processing purpose, deployment context, and actor roles.",
            "MR3": "Clarify automated decision-related and profiling functionality.",
            "MR4": "Describe meaningful human oversight arrangements.",
            "MR5": "Provide fuller vendor documentation for screening.",
            "MR6": "Consider whether further impact assessment is required.",
            "MR7": "Clarify hosting, storage, and transfer/access arrangements.",
            "MR8": "Clarify controller, processor, and possible joint-controller roles.",
        }

        actions = []
        for assessment in selected:
            req_id = assessment["requirement_id"]
            if req_id in action_map:
                actions.append(action_map[req_id])

        return dedupe_keep_order(actions)

    if critical_gap_assessments:
        key_drivers = [format_driver(a) for a in critical_gap_assessments[:3]]
        priority_actions = build_priority_actions(critical_gap_assessments[:3])
        return {
            "overall_risk": "high",
            "recommended_path": "legal_or_dpo_review",
            "summary_rationale": "At least one critical requirement has a potential gap.",
            "key_drivers": key_drivers,
            "priority_actions": priority_actions,
        }

    no_potential_gaps = all(a["status"] != "potential_gap" for a in triggered)
    only_info_gaps = all(a["status"] in {"met", "not_triggered", "insufficient_information"} for a in assessments)

    low_risk_info_only_ids = {"MR2", "MR5", "MR8"}
    only_low_impact_insufficient = all(
        (a["status"] in {"met", "not_triggered"})
        or (a["status"] == "insufficient_information" and a["requirement_id"] in low_risk_info_only_ids)
        for a in assessments
    )

    if no_potential_gaps and only_info_gaps and only_low_impact_insufficient:
        selected = [a for a in triggered if a["status"] == "insufficient_information"][:3]
        key_drivers = [format_driver(a) for a in selected]
        priority_actions = build_priority_actions(selected)
        if not priority_actions:
            priority_actions = ["Request additional documentation and governance details."]
        return {
            "overall_risk": "low",
            "recommended_path": "request_more_information",
            "summary_rationale": "The case does not show substantive screening red flags, but some governance and documentation details remain incomplete.",
            "key_drivers": key_drivers,
            "priority_actions": priority_actions,
        }

    if important_gap_assessments or critical_insufficient_assessments:
        selected = (important_gap_assessments + critical_insufficient_assessments)[:3]
        key_drivers = [format_driver(a) for a in selected]
        priority_actions = build_priority_actions(selected)
        return {
            "overall_risk": "medium",
            "recommended_path": "officer_review",
            "summary_rationale": "There are non-trivial gaps or insufficient information affecting reliable screening.",
            "key_drivers": key_drivers,
            "priority_actions": priority_actions,
        }

    if all(a["status"] in {"met", "not_triggered"} for a in assessments):
        met_drivers = [a for a in triggered if a["status"] == "met"][:3]
        key_drivers = [format_driver(a) for a in met_drivers]
        return {
            "overall_risk": "low",
            "recommended_path": "accept_and_proceed",
            "summary_rationale": "All assessed requirements are met or not triggered.",
            "key_drivers": key_drivers,
            "priority_actions": ["Proceed with the procurement workflow."],
        }

    fallback_selected = triggered[:3]
    key_drivers = [format_driver(a) for a in fallback_selected]
    priority_actions = build_priority_actions(fallback_selected)
    if not priority_actions:
        priority_actions = ["Conduct manual review of the case."]
    return {
        "overall_risk": "medium",
        "recommended_path": "officer_review",
        "summary_rationale": "The case needs manual review because the available signals are mixed.",
        "key_drivers": key_drivers,
        "priority_actions": priority_actions,
    }


# CLI utility

def _load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run requirement mapping over extracted procurement case facts."
    )
    parser.add_argument("extraction_json", help="Path to extracted case JSON")
    parser.add_argument(
        "--requirements",
        help="Path to requirements.json",
        required=True,
    )
    args = parser.parse_args()

    extraction = _load_json(args.extraction_json)
    engine = MappingEngine.from_json_file(args.requirements)

    mapping_output, decision_output = engine.run(extraction)

    input_path = Path(args.extraction_json)
    stem = input_path.stem.replace("_extracted", "")

    mapping_output_path = input_path.with_name(f"{stem}_requirement_mapping.json")
    decision_output_path = input_path.with_name(f"{stem}_decision_output.json")

    with open(mapping_output_path, "w", encoding="utf-8") as f:
        json.dump(mapping_output, f, indent=2, ensure_ascii=False)

    with open(decision_output_path, "w", encoding="utf-8") as f:
        json.dump(decision_output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Requirement mapping output saved to: {mapping_output_path}")
    print(f"[OK] Decision output saved to: {decision_output_path}")


if __name__ == "__main__":
    main()
