# 5. Derived Intermediate Variables Logic

## 5.1 Role of derived intermediate variables

Derived intermediate variables are structured case-level representations used to bridge raw extracted facts and requirement-level assessment.

They do not constitute final legal conclusions.  
Instead, they function as operational proxies that make legal and governance screening logic executable.

In this system, derived intermediate variables are produced from schema-constrained extraction outputs and then reused across multiple requirements in the mapping layer.  
This reduces dependence on free-form interpretation and improves consistency, traceability, and auditability.

## 5.2 Why this layer is needed

Regulatory requirements are not usually mapped directly from raw case text.  
Instead, procurement screening requires a set of intermediate variables that capture relevant properties of the case in a structured and reusable form.

For example, the system does not directly infer a legal conclusion from a sentence in the case text.  
It first derives variables such as `health_data_processing`, `automated_decision_making`, `human_oversight`, or `cross_border_transfer_indicated`, and then uses these variables in requirement-level assessment.

This layer therefore serves two purposes:

1. it operationalises legal and governance concepts into machine-tractable screening variables  
2. it creates a stable bridge between extraction outputs and downstream requirement mapping logic

## 5.3 Derived intermediate variables table

| Derived variable | Derived from | Operational meaning | Used in requirements | Interpretive note |
|---|---|---|---|---|
| `health_data_processing` | Extracted signals about clinical data, monitoring data, diagnostic data, medical images, treatment-related information, or health service context | Indicates that the case involves processing that reveals or concerns health status | MR1, MR4, MR6, MR7 | This is a screening proxy for health-data relevance, not a final legal qualification of all processing details. |
| `biometric_processing` | Extracted signals about facial, fingerprint, iris, voice, gait, or similar features used for identity matching, verification, authentication, or unique identification | Indicates possible identity-related biometric processing | MR1, MR6 | This variable uses a deliberately narrow interpretation. Medical images or physiological signals used only for diagnosis or monitoring should not automatically count as biometric processing. |
| `is_sensitive` | Extracted indicators that the processing involves special category or similarly sensitive data signals | Indicates whether the case includes data that should trigger heightened scrutiny | MR1, MR7 | This variable supports screening-stage sensitivity detection and should not be treated as a substitute for full legal qualification. |
| `legal_basis_clarity` | Extracted statements about legal basis, contractual basis, consent framing, public task framing, or other justificatory language | Indicates whether a recognizable legal basis is clearly described in the materials | MR1 | This variable measures clarity and identifiability, not legal correctness in a final doctrinal sense. |
| `article_9_condition_identified` | Extracted statements about explicit consent, health care provision, public interest in public health, research, or other Article 9-type justifications | Indicates whether a special-category processing condition is explicitly identifiable | MR1 | This variable only captures whether an Article 9-style condition is visible in the materials, not whether it is legally sufficient. |
| `automated_decision_making` | Extracted signals about automated alerts, scores, classifications, rankings, triage outputs, escalation triggers, or similar decision-related outputs | Indicates that the system generates automated outputs capable of guiding or influencing human decisions or actions | MR3, MR4, MR6 | This uses a practical screening interpretation. The variable does not require proof that the system makes the final decision autonomously. |
| `profiling_indicated` | Extracted signals about scoring, classification, prediction, ranking, categorisation, or person-level evaluative outputs derived from personal or health-related inputs | Indicates that the system may perform evaluative or predictive person-level processing relevant to profiling-style concerns | MR3, MR4, MR6 | The word "profiling" need not appear in the text. The variable captures profiling-like functionality for screening purposes. |
| `human_oversight` | Extracted signals about review, override, clinician validation, approval checkpoints, monitoring obligations, or human involvement in workflow | Indicates whether meaningful human oversight arrangements are described | MR3, MR4, MR6 | Human presence alone is not enough. The variable distinguishes between present, limited, unclear, absent, or not-mentioned oversight arrangements. |
| `vendor_documentation_quality` | Extracted signals about the completeness, clarity, specificity, and usability of the submitted vendor materials | Indicates whether the available documentation is sufficient for reliable procurement-stage screening | MR5 | This variable reflects screening adequacy, not final legal compliance. |
| `cloud_hosting_involved` | Extracted references to vendor cloud, hosted infrastructure, cloud environment, cloud nodes, or remote cloud services | Indicates whether the system depends on hosted/cloud infrastructure | MR7 | This variable is relevant because hosted environments often carry transfer, access, and governance implications. |
| `cross_border_transfer_indicated` | Extracted references to offshore hosting, non-local cloud nodes, global caching, overseas support teams, remote access from other jurisdictions, or international infrastructure | Indicates whether cross-border transfer or cross-border access implications are visible | MR6, MR7 | This variable should capture both storage-related and access-related transfer signals. |
| `data_storage_location_clarity` | Extracted references to server location, hosting geography, regional infrastructure, or statements about where data is stored or processed | Indicates whether hosting or storage location is sufficiently clear for screening | MR7 | This variable is about visibility and specificity, not about legal adequacy by itself. |
| `data_controller_identifiable` | Extracted statements indicating whether the procuring organisation or another party is identifiable as controller | Indicates whether the main controller role can be recognized from the materials | MR2, MR8 | This variable supports governance analysis rather than final legal determination. |
| `vendor_role` | Extracted statements suggesting processor, controller, joint controller, sub-processor, or unclear role allocation | Indicates how the vendor is positioned in the processing arrangement | MR2, MR8 | Marketing phrases such as "tool," "platform," or "suggestion engine" are not sufficient unless they imply a legally meaningful role. |
| `joint_controller_possibility` | Extracted statements suggesting shared purpose-setting, shared means determination, secondary training reuse, or other indicators of possible joint controllership | Indicates whether a joint-controller question may need to be considered | MR2, MR8 | This variable functions as a screening alert, not a final Article 26 determination. |
| `procurement_purpose` | Extracted case description of intended use, such as triage, monitoring, diagnostic support, administration, or research | Indicates the operational purpose of the procurement | MR2 | This variable helps anchor requirement applicability and interpretive context. |
| `deployment_context` | Extracted case description of where and how the tool is deployed, such as hospital, home monitoring, clinic, ER workflow, or cloud service | Indicates the use environment and organisational setting | MR2 | This variable supports contextual interpretation of risk, governance, and role allocation. |

## 5.4 Variable derivation logic

The derived intermediate variables are not all of the same type.

They can be grouped into four functional categories:

1. **data-related variables**  
   such as `health_data_processing`, `biometric_processing`, and `is_sensitive`

2. **legal-basis and governance variables**  
   such as `legal_basis_clarity`, `article_9_condition_identified`, `data_controller_identifiable`, and `vendor_role`

3. **automation and oversight variables**  
   such as `automated_decision_making`, `profiling_indicated`, and `human_oversight`

4. **infrastructure and transfer variables**  
   such as `cloud_hosting_involved`, `cross_border_transfer_indicated`, and `data_storage_location_clarity`

This grouping supports modular requirement mapping and reduces duplication in downstream logic.

## 5.5 Interpretive boundary

Derived intermediate variables are not treated as final legal conclusions.  
They are operational screening variables designed to support consistent requirement mapping.

For example, `automated_decision_making = yes` does not mean that Article 22 GDPR definitively applies.  
Similarly, `cross_border_transfer_indicated = yes` does not itself establish unlawful transfer.  
Instead, such variables indicate that the relevant issue is visible and should be considered in downstream requirement and escalation logic.