from openai import OpenAI
import json
import sys
from pathlib import Path

client = OpenAI()

procurement_case_extraction_schema = {
    "type": "json_schema",
    "name": "procurement_case_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "case_metadata",
            "actors",
            "extracted_parameters",
            "missing_information",
            "evidence_spans"
        ],
        "properties": {
            "case_metadata": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "procurement_purpose",
                    "deployment_context"
                ],
                "properties": {
                    "procurement_purpose": {
                        "type": "string",
                        "enum": [
                            "administrative",
                            "clinical_support",
                            "diagnostic",
                            "patient_identification",
                            "triage",
                            "monitoring",
                            "research",
                            "unspecified",
                            "other"
                        ]
                    },
                    "deployment_context": {
                        "type": "string",
                        "enum": [
                            "hospital",
                            "clinic",
                            "emergency_care",
                            "primary_care",
                            "administrative_office",
                            "cross_organizational",
                            "cloud_service",
                            "unspecified",
                            "other"
                        ]
                    }
                }
            },
            "actors": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "procuring_entity",
                    "vendor",
                    "data_controller_identifiable",
                    "vendor_role",
                    "joint_controller_possibility"
                ],
                "properties": {
                    "procuring_entity": {"type": "string"},
                    "vendor": {"type": "string"},
                    "data_controller_identifiable": {
                        "type": "string",
                        "enum": ["yes", "no", "unclear", "not_mentioned"]
                    },
                    "vendor_role": {
                        "type": "string",
                        "enum": [
                            "processor",
                            "controller",
                            "joint_controller",
                            "sub_processor",
                            "unclear",
                            "not_mentioned"
                        ]
                    },
                    "joint_controller_possibility": {
                        "type": "string",
                        "enum": ["yes", "no", "unclear", "not_mentioned"]
                    }
                }
            },
            "extracted_parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "object",
                    "regulatory_logic",
                    "conditions_and_basis",
                    "infrastructure_and_transfers"
                ],
                "properties": {
                    "object": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "data_types_involved",
                            "is_sensitive",
                            "biometric_processing",
                            "health_data_processing"
                        ],
                        "properties": {
                            "data_types_involved": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "health_data",
                                        "biometric_data",
                                        "personal_identifiers",
                                        "demographic_data",
                                        "clinical_notes",
                                        "diagnostic_data",
                                        "behavioral_data",
                                        "usage_data",
                                        "unknown",
                                        "other"
                                    ]
                                }
                            },
                            "is_sensitive": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "biometric_processing": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "health_data_processing": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            }
                        }
                    },
                    "regulatory_logic": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "initial_regulatory_signal",
                            "automated_decision_making",
                            "profiling_indicated",
                            "processing_context_type",
                            "decision_effect_level"
                        ],
                        
                        "properties": {
                            "initial_regulatory_signal": {
                                "type": "string",
                                "enum": [
                                    "potential_prohibition_exception_required",
                                    "potential_obligation",
                                    "potential_permission_with_conditions",
                                    "unclear",
                                    "not_mentioned"
                                ]
                            },
                            "automated_decision_making": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "profiling_indicated": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "processing_context_type": {
    "type": "string",
    "enum": [
        "clinical_care",
        "diagnostic_or_monitoring",
        "occupational_health",
        "employee_wellness",
        "administrative_operations",
        "consumer_or_service_personalisation",
        "mixed",
        "unclear",
        "not_mentioned"
    ]
},
"decision_effect_level": {
    "type": "string",
    "enum": [
        "legal_or_similarly_significant",
        "clinical_or_care_significant",
        "employment_or_benefit_significant",
        "recommendation_only",
        "analytics_only",
        "unclear",
        "not_mentioned"
    ]
}
                            

                        }
                    },
                    "conditions_and_basis": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "legal_basis_clarity",
                            "article_9_condition_identified",
                            "article_9_condition_type",
                            "consent_status",
                            "human_oversight",
                            "vendor_documentation_quality"
                        ],
                        "properties": {
                            "legal_basis_clarity": {
                                "type": "string",
                                "enum": ["clear", "partial", "unclear", "not_provided"]
                            },
                            "article_9_condition_identified": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_applicable", "not_mentioned"]
                            },
                            "article_9_condition_type": {
                                "type": "string",
                                "enum": [
                                    "explicit_consent",
                                    "employment_social_security",
                                    "vital_interests",
                                    "non_profit_body",
                                    "manifestly_public",
                                    "legal_claims",
                                    "substantial_public_interest",
                                    "health_or_social_care",
                                    "public_health",
                                    "research_statistics",
                                    "unclear",
                                    "not_mentioned",
                                    "not_applicable"
                                ]
                            },
                            "consent_status": {
                                "type": "string",
                                "enum": [
                                    "explicit",
                                    "implicit",
                                    "not_obtained",
                                    "unclear",
                                    "not_mentioned"
                                ]
                            },
                            "human_oversight": {
                                "type": "string",
                                "enum": [
                                    "present",
                                    "absent",
                                    "limited",
                                    "unclear",
                                    "not_mentioned"
                                ]
                            },
                            "vendor_documentation_quality": {
                                "type": "string",
                                "enum": [
                                    "high",
                                    "medium",
                                    "low",
                                    "insufficient_information",
                                    "not_provided"
                                ]
                            }
                        }
                    },
                    "infrastructure_and_transfers": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "cloud_hosting_involved",
                            "cross_border_transfer_indicated",
                            "data_storage_location_clarity"
                        ],
                        "properties": {
                            "cloud_hosting_involved": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "cross_border_transfer_indicated": {
                                "type": "string",
                                "enum": ["yes", "no", "unclear", "not_mentioned"]
                            },
                            "data_storage_location_clarity": {
                                "type": "string",
                                "enum": ["clear", "partial", "unclear", "not_provided"]
                            }
                        }
                    }
                }
            },
            "missing_information": {
                "type": "array",
                "items": {"type": "string"}
            },
            "evidence_spans": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "procurement_purpose",
                    "deployment_context",
                    "biometric_processing",
                    "health_data_processing",
                    "automated_decision_making",
                    "profiling_indicated",
                    "processing_context_type",
                    "legal_basis_clarity",
                    "article_9_condition_identified",
                    "article_9_condition_type",
                    "consent_status",
                    "human_oversight",
                    "decision_effect_level",
                    "vendor_documentation_quality",
                    "cloud_hosting_involved",
                    "cross_border_transfer_indicated",
                    "data_storage_location_clarity",
                    "vendor_role",
                    "joint_controller_possibility"
                ],
                "properties": {
                    "processing_context_type": {"type": "string"},
                    "decision_effect_level": {"type": "string"},
                    "procurement_purpose": {"type": "string"},
                    "deployment_context": {"type": "string"},
                    "biometric_processing": {"type": "string"},
                    "health_data_processing": {"type": "string"},
                    "automated_decision_making": {"type": "string"},
                    "profiling_indicated": {"type": "string"},
                    "legal_basis_clarity": {"type": "string"},
                    "article_9_condition_identified": {"type": "string"},
                    "article_9_condition_type": {"type": "string"},
                    "consent_status": {"type": "string"},
                    "human_oversight": {"type": "string"},
                    "vendor_documentation_quality": {"type": "string"},
                    "cloud_hosting_involved": {"type": "string"},
                    "cross_border_transfer_indicated": {"type": "string"},
                    "data_storage_location_clarity": {"type": "string"},
                    "vendor_role": {"type": "string"},
                    "joint_controller_possibility": {"type": "string"}
                }
            }
        }
    }
}

developer_prompt = """
Extract compliance-relevant facts from an IT procurement case.

Rules:
1. Return only structured data matching the schema.
2. Do NOT provide legal advice, risk classification, or final compliance conclusions.
3. Do NOT guess unsupported facts.
4. If information is missing, use values such as "unclear", "not_mentioned", or "not_provided" where appropriate.
5. Fill missing_information with facts needed for later compliance screening but absent from the case.
6. Fill evidence_spans with short supporting excerpts from the case text.
7. Keep evidence excerpts brief and as literal as possible.

Field guidance:
For data_types_involved, use a strict evidence-only interpretation.

Include a data type only when the source text directly states or clearly describes that specific category of data.

Do NOT infer one data category merely from:
- the type of organisation
- the deployment context
- EHR integration
- the fact that patient data is involved
- the fact that the system performs clinical analysis
- another broader data category

In particular:

- Do NOT infer "personal_identifiers" merely because patient data, EHR data, hospital records, or person-level data are involved.

- Do NOT infer "clinical_notes" merely because the system is used in a hospital, clinical workflow, EHR environment, or laboratory setting.

- Do NOT infer "diagnostic_data" merely because the system performs clinical risk classification or is used in healthcare. Include it only when diagnostic results, diagnostic measurements, diagnoses, or equivalent diagnostic information are directly described.

- Do NOT infer "biometric_data" from genetic data, medical images, ECG, physiological signals, or other health data unless biometric identity use is explicitly described.

- Use "other" only when the source text clearly describes a concrete data category that cannot be represented by another available enum value. Do not use "other" merely because the documentation is broad or incomplete.

Do not expand a broad data category into narrower categories unless the narrower category is explicitly supported by the source text.

Examples:

"The system processes patient health information."
-> ["health_data"]

"The system processes names, patient IDs, and health information."
-> ["personal_identifiers", "health_data"]

"The system processes physician-written clinical notes and diagnosis records."
-> ["clinical_notes", "diagnostic_data", "health_data"]

"The system integrates with the hospital EHR."
-> This alone does NOT support "personal_identifiers", "clinical_notes", or "diagnostic_data".

"The system processes laboratory test results."
-> This supports "health_data"; do not automatically add unrelated categories.

When evidence for a specific data category is absent, omit that category rather than inferring it.

For health_data_processing, use a cautious but still screening-oriented interpretation.

Set health_data_processing = "yes" only when the text clearly indicates that the system processes data about a person's physical or mental health, medical condition, diagnosis, treatment, clinical care, clinical monitoring, physiological state, medical images, test results, symptoms, or other information that directly reveals current or past health status.

Also set health_data_processing = "yes" when the text clearly indicates that the system derives or uses person-level health status, medical risk, disease-related condition, or care-related conclusions from the inputs.

Do NOT set health_data_processing = "yes" merely because the case involves:
- a hospital, clinic, or healthcare organisation as the procuring entity
- a workplace wellness, nutrition, fitness, lifestyle, or cafeteria context
- behavioural or usage data that may be health-adjacent
- general recommendations such as healthier choices, wellbeing suggestions, or lifestyle nudges
- opt-in participation or employee benefit schemes
unless the text clearly shows that the system processes or infers actual health status, medical condition, diagnosis, treatment, physiological state, or other person-level health information.

If the text suggests possible health-related inference or a health-adjacent context, but does not clearly show that the system processes or derives actual health status or medical-condition information, use "unclear" rather than "yes".

Set health_data_processing = "no" when the text indicates only operational, behavioural, preference, consumption, or usage data without a clear health-status or medical-condition dimension.
Set health_data_processing = "not_mentioned" when there is no relevant indication at all.

Examples for health_data_processing:
- A system processing diagnosis codes, lab values, and treatment plans -> "yes"
- A tool generating patient deterioration risk from vital signs -> "yes"
- A dermatology model using lesion images for clinical assessment -> "yes"
- A staff cafeteria system analysing meal purchases and suggesting healthier alternatives, without clinical or diagnostic data -> "unclear"
- A wellness app tracking general preferences or purchase habits, without clear health-status inference -> "unclear"
- A canteen analytics tool using only aggregated menu demand data -> "no"

For human_oversight, use a strict and operational interpretation.

Set human_oversight = "present" only when the text clearly indicates meaningful human review, validation, approval, intervention, or override capability in relation to the system's output or action.

This usually requires evidence that a human can do one or more of the following:
- review the system's output before action is taken
- approve, confirm, or validate the output before downstream action
- intervene in the workflow before the system-triggered action occurs
- override, block, reverse, or materially correct the system's output or action
- exercise real discretion rather than merely receiving a notification

Set human_oversight = "limited" when some human involvement is described, but it appears weak, delayed, formalistic, or not clearly meaningful.
Examples include:
- post hoc review only
- human monitoring without clear approval power
- alerts sent to staff without clear ability to prevent or override the action
- occasional spot checks or audit after deployment
- vague statements that a clinician or staff member is "in the loop" without operational detail

Set human_oversight = "unclear" when the text suggests possible human involvement, escalation, notification, or operational follow-up, but does not clearly show meaningful review, approval, intervention, or override capability.

Set human_oversight = "absent" when the text clearly indicates that the system acts automatically without meaningful human review or intervention.

Set human_oversight = "not_mentioned" when there is no relevant indication at all.

Important:
- Do NOT treat a notification, alert, escalation, or referral to a human as automatically equivalent to meaningful human oversight.
- Do NOT treat post-action human response as the same as pre-action review or pre-action intervention.
- If the system acts first and a human is only informed afterwards, prefer "limited" or "unclear", not "present".
- If the text does not clearly state that a human can review or override the relevant action, do not infer "present".

Examples for human_oversight:
- "A clinician must approve the recommendation before it is added to the patient record." -> "present"
- "The system flags cases for nurse review before any escalation decision is executed." -> "present"
- "The system automatically locks the door and alerts the rapid response team." -> "unclear"
- "An alert is sent to staff after the automated action is triggered." -> "limited"
- "Staff may monitor dashboard outputs, but no approval or override process is described." -> "limited"
- No mention of review, approval, override, or intervention -> "not_mentioned"

When human oversight is not clearly established, include missing-information items about whether a human reviews the output before action, whether any approval checkpoint exists, and whether any override or reversal mechanism is available.

For evidence_spans.human_oversight, provide a short excerpt that directly supports review, approval, override, intervention, or lack thereof.
Do NOT use a generic alert, escalation, or notification phrase as evidence for "present" unless it clearly supports meaningful pre-action or real override-capable human oversight.

For evidence_spans.health_data_processing, provide a short excerpt that directly supports actual health-status, medical-condition, treatment, clinical-monitoring, physiological, or clearly health-inference-related processing.
Do NOT use a generic wellness, nutrition, hospital, or healthier-lifestyle phrase as evidence for "yes" unless it clearly supports health-status or medical-condition processing.

For biometric_processing, use a narrow interpretation.

Set biometric_processing = "yes" only when the case text indicates that physiological, facial, fingerprint, voice, iris, gait, or similar human features are processed for the purpose of uniquely identifying, authenticating, verifying, or matching a person's identity.

Do NOT set biometric_processing = "yes" merely because the system processes medical images, skin lesion photos, ECG or heart-rate data, or other health-related measurements, unless the text indicates that such data is used for identity recognition, authentication, or biometric matching.

If the text describes images, physiological signals, or bodily data used for diagnosis, monitoring, triage, or clinical assessment only, then biometric_processing should normally be "no" or "unclear", not "yes".

Use "unclear" only when the text suggests possible biometric identity-related use but does not make that purpose explicit.
Use "not_mentioned" when there is no relevant indication at all.

Examples for biometric_processing:
- A facial recognition system used to verify patient identity at check-in -> "yes"
- A fingerprint scanner used for login or authentication -> "yes"
- A skin lesion photo used for dermatology risk scoring only -> "no"
- ECG and heart-rate monitoring used for arrhythmia detection only -> "no"
- A patient photo used for diagnostic review, without identity matching -> "no"

For evidence_spans.biometric_processing, only provide a span that directly supports identity-related biometric use.
Do not reuse general health-data or body-signal descriptions as biometric evidence unless the text explicitly links them to identification, verification, authentication, or matching.

For automated_decision_making, use a practical but person-affecting interpretation.

Set automated_decision_making = "yes" only when the text indicates that the system automatically generates a decision, recommendation, score, alert, classification, ranking, priority level, escalation trigger, or similar output about a person, and that output may influence action toward that person.

Examples of person-affecting outputs include:
- a risk score about a patient
- a red/green triage classification for a person
- a high-priority alert about a patient
- a ranking or category assigned to an individual
- an automated recommendation that affects treatment flow, review priority, escalation, or access to a service for a person

Do NOT set automated_decision_making = "yes" merely because the system performs:
- inventory prediction
- sales forecasting
- demand planning
- stock optimisation
- operational analytics
- aggregate resource planning
unless the text clearly shows that the output is assigned to a person or triggers action toward a person.

Do not require the text to prove that the system makes the final legal or clinical decision by itself. At screening stage, it is enough that the system generates a person-affecting automated output that is decision-related or action-guiding.

Set automated_decision_making = "no" when the system output is only operational, aggregate, or item-level and not person-affecting.
Set automated_decision_making = "unclear" only when the text is too vague to tell whether the output is person-affecting.

For profiling_indicated, use a person-level interpretation.

Set profiling_indicated = "yes" only when the text indicates that the system evaluates, scores, categorises, predicts, ranks, or assesses an identifiable person or a group of persons based on personal data, behavioural data, physiological data, health data, demographic data, or similar person-related inputs.

Examples include:
- a melanoma risk score for a patient
- a triage priority category for a patient
- an attendance risk score for an employee
- a fraud score for a customer
- a ranking of individuals for review or intervention

Do NOT set profiling_indicated = "yes" for:
- product demand forecasting
- stock optimisation
- cafeteria sales prediction
- inventory prediction
- aggregate trend analysis
- predictions about goods, locations, or organisational resources rather than people

Do not require the word "profiling" to appear explicitly.
If the system analyses data only to forecast demand for products, meals, supplies, stock levels, or other operational resources, profiling_indicated should normally be "no", not "yes".

Set profiling_indicated = "no" when the output is operational, aggregate, or resource-focused rather than person-focused.
Set profiling_indicated = "unclear" only when the text suggests person-level evaluation but does not make that sufficiently clear.

Examples:
- "The AI gives an instant melanoma risk score" -> automated_decision_making = "yes", profiling_indicated = "yes"
- "The system triggers a high-priority alert for arrhythmia" -> automated_decision_making = "yes", profiling_indicated = "yes"
- "The tool predicts how much milk and bread the hospital should order next week" -> automated_decision_making = "no", profiling_indicated = "no"
- "The system forecasts cafeteria demand based on past purchases" -> automated_decision_making = "no", profiling_indicated = "no"
- "The tool stores records but does not score, rank, classify, or alert people" -> automated_decision_making = "no", profiling_indicated = "no"


If automated_decision_making = "no", the evidence span for automated_decision_making should normally be empty unless the text explicitly states the absence of person-affecting automated outputs.

If profiling_indicated = "no", the evidence span for profiling_indicated should normally be empty unless the text explicitly states the absence of person-level evaluation.

For evidence_spans.automated_decision_making and evidence_spans.profiling_indicated, prefer short excerpts that directly show person-level scoring, categorisation, alerts, rankings, predictions, or action-guiding outputs.
Do not use generic forecasting, inventory-planning, stock-optimisation, or aggregate demand language as evidence unless it clearly concerns a person.

For processing_context_type, identify the substantive context of the processing, not just the organisation type.

Use:
- "clinical_care" when the system supports treatment, care delivery, or patient management for identified persons
- "diagnostic_or_monitoring" when the system supports diagnosis, risk detection, deterioration monitoring, or physiological assessment
- "occupational_health" when the processing concerns employee health, fitness-for-work, workplace exposure, or occupational medical functions
- "employee_wellness" when the system supports general staff wellbeing, nutrition, lifestyle, or wellness initiatives without clear clinical or occupational-health determination
- "administrative_operations" when the processing is mainly operational, logistical, HR, procurement, scheduling, stock, or service administration
- "consumer_or_service_personalisation" when the system mainly personalises recommendations, suggestions, or user experience without clear clinical, occupational-health, or legal-effect significance
- "mixed" when the text clearly supports more than one of the above in a material way
- "unclear" when the context cannot be determined confidently
- "not_mentioned" when there is no useful indication at all

Do NOT infer "clinical_care" merely because the procuring entity is a hospital or clinic.
A hospital cafeteria, staff wellbeing, or internal operations case may still be "employee_wellness" or "administrative_operations".

For evidence_spans.processing_context_type, provide a short excerpt that directly supports the functional context of the system.

For decision_effect_level, assess the likely significance of the system's output for the affected person.

Use:
- "legal_or_similarly_significant" when the output may determine or strongly influence access, eligibility, rights, obligations, or comparably serious effects
- "clinical_or_care_significant" when the output may influence diagnosis, treatment, triage, escalation, monitoring intensity, or other clinically meaningful action
- "employment_or_benefit_significant" when the output may influence staff evaluation, workplace treatment, benefits, fitness-for-work assessment, or employment-related action
- "recommendation_only" when the output is mainly advisory, suggestive, or nudging, without clear evidence of materially significant consequence
- "analytics_only" when the output is aggregate, descriptive, dashboard-based, or operational rather than action-guiding toward a person
- "unclear" when the text suggests person-level output but does not make its effect sufficiently clear
- "not_mentioned" when no relevant indication is available

Do NOT treat a generic recommendation, wellness suggestion, healthier alternative, or lifestyle nudge as automatically legally or clinically significant.
If the output mainly suggests options without clear downstream consequence, prefer "recommendation_only".

For evidence_spans.decision_effect_level, provide a short excerpt that directly supports the likely significance of the output.


"""

case_file = sys.argv[1] if len(sys.argv) > 1 else "case1.txt"
case_path = Path(case_file)

if not case_path.exists():
    raise FileNotFoundError(f"Case file not found: {case_path}")


with open(case_path, "r", encoding="utf-8") as f:
    case_text = f.read()

response = client.responses.create(
    model="gpt-5.4-mini",
    input=[
        {"role": "developer", "content": developer_prompt},
        {"role": "user", "content": case_text}
    ],
    text={
        "format": procurement_case_extraction_schema
    }
)

print("=== RAW OUTPUT TEXT ===")
print(response.output_text)

parsed = json.loads(response.output_text)

print("\n=== PARSED JSON ===")
print(json.dumps(parsed, indent=2, ensure_ascii=False))

output_file = f"{case_path.stem}_extracted.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(parsed, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Extracted JSON saved to: {output_file}")