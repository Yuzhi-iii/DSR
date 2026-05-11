from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


UNRESOLVED_VALUES = {
    None,
    "",
    "unclear",
    "not_mentioned",
    "not_provided",
    "partial",
    "insufficient_information",
    "unspecified",
    "other",
}


FIELD_CLARIFICATION_RULES = [
    {
        "field_path": "case_metadata.procurement_purpose",
        "topic": "Procurement purpose",
        "trigger_values": ["unspecified", "other", "unclear", "not_mentioned"],
        "question": (
            "What is the intended purpose of the AI system in this procurement, "
            "for example diagnostic support, monitoring, triage, administration, research, or another use?"
        ),
        "material_prompt": (
            "You may upload procurement notes, business case materials, product descriptions, "
            "or workflow documents that explain the intended purpose."
        ),
        "priority": 30,
    },
    {
        "field_path": "case_metadata.deployment_context",
        "topic": "Deployment context",
        "trigger_values": ["unspecified", "other", "unclear", "not_mentioned"],
        "question": (
            "Where and how will the system be deployed, for example hospital, clinic, "
            "emergency care, cloud service, primary care, or cross-organisational use?"
        ),
        "material_prompt": (
            "You may upload deployment notes, workflow descriptions, architecture diagrams, "
            "or procurement materials describing the use environment."
        ),
        "priority": 30,
    },
    {
        "field_path": "actors.data_controller_identifiable",
        "topic": "Controller identification",
        "trigger_values": ["no", "unclear", "not_mentioned"],
        "question": (
            "Which organisation determines the purposes and means of the processing, "
            "or is this not yet established in the procurement materials?"
        ),
        "material_prompt": (
            "You may upload DPA terms, privacy governance notes, procurement questionnaires, "
            "or contract excerpts describing controller responsibility."
        ),
        "priority": 20,
    },
    {
        "field_path": "actors.vendor_role",
        "topic": "Vendor role",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "What role does the vendor have in relation to personal data, for example processor, "
            "controller, joint controller, or sub-processor?"
        ),
        "material_prompt": (
            "You may upload the data processing agreement, vendor terms, contract clauses, "
            "or supplier questionnaire responses."
        ),
        "priority": 20,
    },
    {
        "field_path": "actors.joint_controller_possibility",
        "topic": "Possible joint-controller role",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Is there any indication that the procuring entity and vendor jointly determine "
            "the purposes or means of processing, or that the vendor reuses data for its own purposes?"
        ),
        "material_prompt": (
            "You may upload contract terms, product terms, AI training/reuse terms, "
            "or governance notes addressing shared decision-making or data reuse."
        ),
        "priority": 25,
    },
    {
        "field_path": "extracted_parameters.object.is_sensitive",
        "topic": "Sensitive data involvement",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Does the system process sensitive or special-category data, such as health data, "
            "biometric identification data, or other sensitive personal data?"
        ),
        "material_prompt": (
            "You may upload data inventory, DPIA materials, product documentation, "
            "or vendor data-processing descriptions."
        ),
        "priority": 10,
    },
    {
        "field_path": "extracted_parameters.object.health_data_processing",
        "topic": "Health data processing",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Does the system process or infer information about a person's health status, "
            "medical condition, diagnosis, treatment, clinical monitoring, symptoms, test results, "
            "or care-related risk?"
        ),
        "material_prompt": (
            "You may upload clinical workflow notes, product documentation, data dictionaries, "
            "or model input/output descriptions."
        ),
        "priority": 10,
    },
    {
        "field_path": "extracted_parameters.object.biometric_processing",
        "topic": "Biometric processing",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Does the system process facial, fingerprint, voice, iris, gait, or similar features "
            "for identification, authentication, verification, or matching of a person?"
        ),
        "material_prompt": (
            "You may upload identity-verification documentation, access-control descriptions, "
            "or technical documentation on biometric matching."
        ),
        "priority": 10,
    },
    {
        "field_path": "extracted_parameters.regulatory_logic.automated_decision_making",
        "topic": "Automated decision-related functionality",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Does the system automatically generate a score, classification, recommendation, "
            "alert, priority level, ranking, escalation trigger, or other output about an individual?"
        ),
        "material_prompt": (
            "You may upload product documentation, workflow descriptions, model output examples, "
            "or clinical/operational process notes."
        ),
        "priority": 10,
    },
    {
        "field_path": "extracted_parameters.regulatory_logic.profiling_indicated",
        "topic": "Profiling or person-level evaluation",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Does the system evaluate, score, rank, categorise, predict, or assess an identifiable "
            "person or group of persons based on personal, behavioural, demographic, health, "
            "or similar data?"
        ),
        "material_prompt": (
            "You may upload model documentation, use-case descriptions, output examples, "
            "or product materials describing scoring or classification."
        ),
        "priority": 15,
    },
    {
        "field_path": "extracted_parameters.regulatory_logic.processing_context_type",
        "topic": "Processing context",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "What is the substantive processing context, for example clinical care, diagnostic "
            "or monitoring, occupational health, employee wellness, administrative operations, "
            "or consumer/service personalisation?"
        ),
        "material_prompt": (
            "You may upload workflow descriptions, business case documents, product descriptions, "
            "or user journey materials."
        ),
        "priority": 25,
    },
    {
        "field_path": "extracted_parameters.regulatory_logic.decision_effect_level",
        "topic": "Decision effect level",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "What practical effect can the system output have on affected persons, for example "
            "clinical escalation, treatment flow, access to services, employment or benefits, "
            "or only low-impact recommendations or analytics?"
        ),
        "material_prompt": (
            "You may upload workflow documents, escalation protocols, product descriptions, "
            "or governance notes explaining how outputs are used."
        ),
        "priority": 15,
    },
    {
        "field_path": "extracted_parameters.conditions_and_basis.legal_basis_clarity",
        "topic": "Legal basis",
        "trigger_values": ["unclear", "not_provided", "partial"],
        "question": (
            "Is a legal basis for the processing identified in the available materials, "
            "for example public task, contract, legal obligation, legitimate interests, consent, "
            "or another basis?"
        ),
        "material_prompt": (
            "You may upload privacy notices, DPIA materials, legal basis notes, procurement "
            "governance documents, or DPA materials."
        ),
        "priority": 5,
    },
    {
        "field_path": "extracted_parameters.conditions_and_basis.article_9_condition_identified",
        "topic": "Article 9 condition",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "If special-category data such as health data is involved, is an Article 9 condition "
            "identified, such as health or social care, public health, research, explicit consent, "
            "or substantial public interest?"
        ),
        "material_prompt": (
            "You may upload legal basis notes, DPIA materials, privacy notices, or governance "
            "documents addressing special-category data."
        ),
        "priority": 5,
        "only_if_any": [
            {
                "field_path": "extracted_parameters.object.health_data_processing",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.biometric_processing",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.is_sensitive",
                "values": ["yes", "unclear"],
            },
        ],
    },
    {
        "field_path": "extracted_parameters.conditions_and_basis.article_9_condition_type",
        "topic": "Article 9 condition type",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Which Article 9 condition is relied on, if special-category data is involved?"
        ),
        "material_prompt": (
            "You may upload legal basis notes, DPIA materials, privacy notices, or governance "
            "documents addressing special-category data."
        ),
        "priority": 6,
        "only_if_any": [
            {
                "field_path": "extracted_parameters.object.health_data_processing",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.biometric_processing",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.is_sensitive",
                "values": ["yes", "unclear"],
            },
        ],
    },
    {
        "field_path": "extracted_parameters.conditions_and_basis.human_oversight",
        "topic": "Human oversight",
        "trigger_values": ["absent", "limited", "unclear", "not_mentioned"],
        "question": (
            "Is there a meaningful human review, approval, intervention, or override process "
            "before the system output leads to action?"
        ),
        "material_prompt": (
            "You may upload workflow documents, clinical review procedures, governance policies, "
            "standard operating procedures, or escalation protocols."
        ),
        "priority": 5,
        "only_if_any": [
            {
                "field_path": "extracted_parameters.regulatory_logic.automated_decision_making",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.regulatory_logic.profiling_indicated",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.health_data_processing",
                "values": ["yes"],
            },
            {
                "field_path": "extracted_parameters.regulatory_logic.decision_effect_level",
                "values": [
                    "legal_or_similarly_significant",
                    "clinical_or_care_significant",
                    "employment_or_benefit_significant",
                    "unclear",
                ],
            },
        ],
    },
    {
        "field_path": "extracted_parameters.conditions_and_basis.vendor_documentation_quality",
        "topic": "Vendor documentation quality",
        "trigger_values": ["low", "medium", "insufficient_information", "not_provided", "unclear", "not_mentioned"],
        "question": (
            "What vendor documentation is available for this system, such as technical documentation, "
            "security documentation, model documentation, data-processing documentation, or governance materials?"
        ),
        "material_prompt": (
            "You may upload vendor documentation, security documents, AI system documentation, "
            "supplier questionnaire responses, or DPIA-supporting materials."
        ),
        "priority": 20,
    },
    {
        "field_path": "extracted_parameters.infrastructure_and_transfers.cloud_hosting_involved",
        "topic": "Cloud hosting",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Is the system hosted in the cloud or otherwise dependent on remote hosted infrastructure?"
        ),
        "material_prompt": (
            "You may upload architecture documents, hosting statements, cloud service descriptions, "
            "or vendor infrastructure documentation."
        ),
        "priority": 35,
    },
    {
        "field_path": "extracted_parameters.infrastructure_and_transfers.cross_border_transfer_indicated",
        "topic": "Cross-border transfer or access",
        "trigger_values": ["unclear", "not_mentioned"],
        "question": (
            "Do the materials indicate any cross-border transfer, offshore hosting, overseas support access, "
            "or remote access from another jurisdiction?"
        ),
        "material_prompt": (
            "You may upload hosting statements, transfer impact materials, DPA terms, support access terms, "
            "or vendor infrastructure documentation."
        ),
        "priority": 10,
        "only_if_any": [
            {
                "field_path": "extracted_parameters.infrastructure_and_transfers.cloud_hosting_involved",
                "values": ["yes", "unclear", "not_mentioned"],
            },
            {
                "field_path": "extracted_parameters.object.is_sensitive",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.health_data_processing",
                "values": ["yes", "unclear"],
            },
        ],
    },
    {
        "field_path": "extracted_parameters.infrastructure_and_transfers.data_storage_location_clarity",
        "topic": "Data storage location",
        "trigger_values": ["unclear", "not_provided"],
        "question": (
            "Where will the relevant data be stored or processed, and is the storage or processing "
            "location clearly identified?"
        ),
        "material_prompt": (
            "You may upload hosting statements, architecture documents, regional hosting terms, "
            "or vendor infrastructure documentation."
        ),
        "priority": 10,
        "only_if_any": [
            {
                "field_path": "extracted_parameters.infrastructure_and_transfers.cloud_hosting_involved",
                "values": ["yes", "unclear", "not_mentioned"],
            },
            {
                "field_path": "extracted_parameters.object.is_sensitive",
                "values": ["yes", "unclear"],
            },
            {
                "field_path": "extracted_parameters.object.health_data_processing",
                "values": ["yes", "unclear"],
            },
        ],
    },
]


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data

    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default

    return current


def value_matches(value: Any, trigger_values: List[Any]) -> bool:
    if isinstance(value, list):
        return any(item in trigger_values for item in value)
    return value in trigger_values


def passes_context_gate(extraction: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    Optional context gate.

    Some questions should only appear when they are contextually relevant.
    This prevents the system from asking for Article 9 or transfer materials
    just because a field is technically unresolved.
    """
    only_if_any = rule.get("only_if_any")
    if not only_if_any:
        return True

    for condition in only_if_any:
        field_value = get_nested(extraction, condition["field_path"])
        if value_matches(field_value, condition["values"]):
            return True

    return False


def build_question_from_rule(
    extraction: Dict[str, Any],
    rule: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    field_path = rule["field_path"]
    current_value = get_nested(extraction, field_path)

    if not value_matches(current_value, rule["trigger_values"]):
        return None

    if not passes_context_gate(extraction, rule):
        return None

    evidence_span = get_evidence_span(extraction, field_path)

    return {
        "question_id": f"CQ_{field_path.replace('.', '_').upper()}",
        "topic": rule["topic"],
        "question": rule["question"],
        "material_prompt": rule["material_prompt"],
        "field_path": field_path,
        "current_value": current_value,
        "evidence_span": evidence_span,
        "priority": rule.get("priority", 100),
        "answer_options": [
            "direct_answer_provided",
            "additional_material_uploaded",
            "no_additional_information",
        ],
    }


def get_evidence_span(extraction: Dict[str, Any], field_path: str) -> str:
    evidence = extraction.get("evidence_spans", {})
    if not isinstance(evidence, dict):
        return ""

    if field_path in evidence:
        value = evidence[field_path]
        return value if isinstance(value, str) else ""

    short_key = field_path.split(".")[-1]
    value = evidence.get(short_key, "")
    return value if isinstance(value, str) else ""


def generate_clarification_questions(
    extraction: Dict[str, Any],
    max_questions: int = 8,
) -> List[Dict[str, Any]]:
    """
    Generate field-level clarification questions from unresolved extraction outputs.

    This function asks only about fields that are actually missing, unclear,
    partial, not provided, or otherwise unresolved.
    """
    questions: List[Dict[str, Any]] = []

    for rule in FIELD_CLARIFICATION_RULES:
        question = build_question_from_rule(extraction, rule)
        if question:
            questions.append(question)

    missing_information = extraction.get("missing_information", [])
    if isinstance(missing_information, list):
        for index, item in enumerate(missing_information):
            if not isinstance(item, str) or not item.strip():
                continue

            questions.append(
                {
                    "question_id": f"CQ_MISSING_INFORMATION_{index + 1}",
                    "topic": "Missing information",
                    "question": item.strip(),
                    "material_prompt": (
                        "You may provide a short answer or upload supporting material "
                        "addressing this missing information."
                    ),
                    "field_path": "missing_information",
                    "current_value": "missing",
                    "evidence_span": "",
                    "priority": 15,
                    "answer_options": [
                        "direct_answer_provided",
                        "additional_material_uploaded",
                        "no_additional_information",
                    ],
                }
            )

    questions.sort(key=lambda q: (q.get("priority", 100), q["question_id"]))

    return questions[:max_questions]


def build_clarification_summary(
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, str],
    direct_answers: Optional[Dict[str, str]] = None,
) -> str:
    direct_answers = direct_answers or {}

    lines = [
        "=== USER CLARIFICATION RESPONSES ===",
        "",
        "The user was asked targeted clarification questions only for fields that were missing, unclear, partial, not provided, or otherwise unresolved in the first-pass extraction.",
        "",
    ]

    for question in questions:
        qid = question["question_id"]
        answer = user_answers.get(qid, "not_answered")
        direct_answer = direct_answers.get(qid, "").strip()

        lines.extend(
            [
                f"Question ID: {qid}",
                f"Topic: {question['topic']}",
                f"Related field: {question.get('field_path', '')}",
                f"First-pass value: {question.get('current_value', '')}",
                f"Question: {question['question']}",
                f"User selection: {answer}",
            ]
        )

        if direct_answer:
            lines.append(f"User direct answer: {direct_answer}")

        lines.append("")

    return "\n".join(lines)


def combine_case_and_supplements(
    original_case_text: str,
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, str],
    supplementary_texts: Dict[str, str],
    direct_answers: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build one combined text input for the final extraction pipeline.
    """
    parts = [
        "=== ORIGINAL CASE DESCRIPTION ===",
        original_case_text.strip(),
        "",
        build_clarification_summary(
            questions=questions,
            user_answers=user_answers,
            direct_answers=direct_answers,
        ),
        "",
        "=== SUPPLEMENTARY MATERIALS PROVIDED BY USER ===",
        "",
    ]

    if supplementary_texts:
        for filename, text in supplementary_texts.items():
            parts.extend(
                [
                    f"--- Supplementary file: {filename} ---",
                    text.strip(),
                    "",
                ]
            )
    else:
        parts.append("No supplementary material was uploaded.")

    return "\n".join(parts)


def write_combined_case_file(
    output_path: str | Path,
    original_case_text: str,
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, str],
    supplementary_texts: Dict[str, str],
    direct_answers: Optional[Dict[str, str]] = None,
) -> Path:
    output_path = Path(output_path)

    combined_text = combine_case_and_supplements(
        original_case_text=original_case_text,
        questions=questions,
        user_answers=user_answers,
        supplementary_texts=supplementary_texts,
        direct_answers=direct_answers,
    )

    output_path.write_text(combined_text, encoding="utf-8")
    return output_path