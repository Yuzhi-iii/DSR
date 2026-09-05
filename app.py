import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st

from clarification_engine import (
    generate_clarification_questions,
    write_combined_case_file,
)

st.set_page_config(
    page_title="AI Compliance Screener",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ AI Procurement Compliance Screening")
st.markdown("Preliminary screening support for AI-enabled health-data procurement.")

UPLOAD_DIR = Path("temp_uploads")
REQUIREMENTS_PATH = "requirements.json"


def safe_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name or "uploaded_case.txt"


def extract_section(text: str, section_name: str) -> str:
    pattern = rf"## {re.escape(section_name)}\n(.*?)(?=\n##\s|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No specific data found for this section."


def run_initial_extraction(case_path: Path) -> Path:
    result = subprocess.run(
        [sys.executable, "full_schema_extraction.py", str(case_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Initial extraction failed.")
    extracted_path = Path(f"{case_path.stem}_extracted.json")
    if not extracted_path.exists():
        raise FileNotFoundError(f"Expected extraction output not found: {extracted_path}")
    return extracted_path


def run_final_pipeline(case_path: Path, requirements_path: str = REQUIREMENTS_PATH) -> Path:
    result = subprocess.run(
        [sys.executable, "run_full_pipeline.py", str(case_path), requirements_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Final pipeline failed.")
    report_path = Path(f"{case_path.stem}_report.md")
    if not report_path.exists():
        raise FileNotFoundError(f"Expected final report output not found: {report_path}")
    return report_path


def output_paths_for_case(case_path: Path) -> dict:
    stem = case_path.stem
    return {
        "extracted": Path(f"{stem}_extracted.json"),
        "mapping": Path(f"{stem}_requirement_mapping.json"),
        "decision": Path(f"{stem}_decision_output.json"),
        "report": Path(f"{stem}_report.md"),
    }


def load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def humanize_path(path: str) -> str:
    labels = {
        "legal_or_dpo_review": "Legal or DPO review",
        "officer_review": "Officer review",
        "accept_and_proceed": "Accept and proceed",
        "request_more_information": "Request more information",
        "halt_or_manual_review": "Halt or manual review",
    }
    return labels.get(path, path.replace("_", " ").strip().title())


def extract_requirement_id(driver: str) -> str:
    match = re.match(r"^(MR\d+)\b", str(driver).strip())
    return match.group(1) if match else ""


def derive_impact_assessment_signal(requirement_mapping: dict) -> tuple[str, str]:
    assessments = requirement_mapping.get("requirement_assessments", [])
    mr6 = next(
        (item for item in assessments if item.get("requirement_id") == "MR6"),
        None,
    )

    if not mr6 or not mr6.get("triggered"):
        return "Not triggered", "MR6 not triggered"

    status = mr6.get("status")
    if status == "potential_gap":
        return "Triggered", "MR6 impact-assessment escalation condition"
    if status == "insufficient_information":
        return "Review needed", "MR6 requires further assessment"
    if status == "met":
        return "No unresolved trigger", "MR6 assessed as met"

    return "Review needed", f"MR6 status: {status or 'unknown'}"


def display_structured_outcome(case_path: Path) -> None:
    paths = output_paths_for_case(case_path)
    decision = load_json_if_exists(paths["decision"])
    mapping = load_json_if_exists(paths["mapping"])

    if not decision:
        return

    st.subheader("Screening Outcome")
    st.caption(
        "These values are read directly from the rule-based decision and requirement-mapping outputs."
    )

    impact_label, impact_detail = derive_impact_assessment_signal(mapping)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall risk", str(decision.get("overall_risk", "unknown")).upper())
    with col2:
        st.metric(
            "Recommended path",
            humanize_path(str(decision.get("recommended_path", "unknown"))),
        )
    with col3:
        st.metric("Impact assessment signal", impact_label)
        st.caption(impact_detail)

    key_drivers = decision.get("key_drivers", [])
    if key_drivers:
        st.markdown("**Escalation drivers:** " + " · ".join(map(str, key_drivers)))

    assessments = [
        item
        for item in mapping.get("requirement_assessments", [])
        if item.get("triggered")
    ]

    if assessments:
        driver_ids = {
            extract_requirement_id(driver)
            for driver in key_drivers
            if extract_requirement_id(driver)
        }
        rows = []
        for item in assessments:
            rid = item.get("requirement_id", "")
            rows.append(
                {
                    "Requirement": rid,
                    "Assessment": item.get("status", ""),
                    "Role in outcome": "Escalation driver" if rid in driver_ids else "Other assessment",
                    "Requirement name": item.get("name", ""),
                }
            )

        with st.expander("View requirement assessments"):
            st.dataframe(rows, use_container_width=True, hide_index=True)

    if decision.get("summary_rationale"):
        st.caption(decision["summary_rationale"])


def display_report(report_path: Path, uploaded_name: str, case_path: Path) -> None:
    report_md = report_path.read_text(encoding="utf-8")

    st.divider()
    st.subheader("📝 Compliance Assessment Results")

    display_structured_outcome(case_path)
    st.markdown("---")

    st.info("### Executive Summary")
    st.markdown(extract_section(report_md, "Executive Summary"))

    sections = [
        "Key Screening Concerns",
        "Priority Actions",
        "Structured Facts",
        "Key Missing Information",
        "Triggered Rules",
        "Legal References",
    ]

    for sec in sections:
        with st.expander(f"View {sec}"):
            st.markdown(extract_section(report_md, sec))

    st.markdown("---")
    st.success("### Final Recommendation")
    st.markdown(extract_section(report_md, "Final Recommendation"))

    st.download_button(
        label="📥 Download Full Report (.md)",
        data=report_md,
        file_name=f"Compliance_Report_{uploaded_name.replace('.txt', '.md')}",
        mime="text/markdown",
    )


def reset_session() -> None:
    keys = [
        "stage",
        "case_path",
        "uploaded_name",
        "original_case_text",
        "extracted_path",
        "clarification_questions",
        "report_path",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def initialise_session_state() -> None:
    defaults = {
        "stage": "upload",
        "case_path": None,
        "uploaded_name": "",
        "original_case_text": "",
        "extracted_path": None,
        "clarification_questions": [],
        "report_path": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_uploaded_case(uploaded_file) -> Path:
    UPLOAD_DIR.mkdir(exist_ok=True)
    safe_name = safe_filename(uploaded_file.name)
    case_path = UPLOAD_DIR / f"case_{safe_name}"
    case_path.write_bytes(uploaded_file.getbuffer())
    return case_path


def read_uploaded_text_file(uploaded_file) -> str:
    return uploaded_file.getvalue().decode("utf-8")


def grouped_clarification_topics(questions: list) -> list[str]:
    group_map = {
        "Legal basis": "Legal basis / Article 9 condition",
        "Article 9 condition": "Legal basis / Article 9 condition",
        "Article 9 condition type": "Legal basis / Article 9 condition",
        "Controller identification": "Controller / processor responsibilities",
        "Vendor role": "Controller / processor responsibilities",
        "Possible joint-controller role": "Controller / processor responsibilities",
        "Cloud hosting": "Hosting / transfer information",
        "Cross-border transfer or access": "Hosting / transfer information",
        "Data storage location": "Hosting / transfer information",
        "Missing information": "Other documentation gaps",
    }

    topics = []
    for question in questions:
        raw_topic = question.get("topic", "Additional information")
        topic = group_map.get(raw_topic, raw_topic)
        if topic not in topics:
            topics.append(topic)
    return topics


@st.dialog("Additional information may be needed")
def show_clarification_dialog(questions: list) -> None:
    st.write("The current documentation does not clearly describe:")

    for topic in grouped_clarification_topics(questions):
        st.markdown(f"- {topic}")

    st.caption(
        "You can provide more material now, or continue with the current information. "
        "Unresolved gaps will remain visible in the screening output."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add information", type="primary", use_container_width=True):
            st.session_state.stage = "supplementary_information"
            st.rerun()
    with col2:
        if st.button("Continue with current information", use_container_width=True):
            st.session_state.stage = "analysis_pending"
            st.rerun()


with st.sidebar:
    st.header("Control Panel")

    if st.button("🗑️ Clear Cache"):
        if UPLOAD_DIR.exists():
            shutil.rmtree(UPLOAD_DIR)

        for pattern in [
            "temp_*",
            "*_extracted.json",
            "*_requirement_mapping.json",
            "*_decision_output.json",
            "*_report.md",
        ]:
            for p in Path(".").glob(pattern):
                if p.is_file():
                    p.unlink()

        reset_session()
        st.success("Cache cleared!")

    st.divider()
    st.caption("v1.6 | Presentation-aligned UI")


initialise_session_state()

uploaded_file = st.file_uploader("Upload Case Description (.txt)", type=["txt"])

if uploaded_file and st.session_state.stage == "upload":
    case_path = save_uploaded_case(uploaded_file)

    st.session_state.case_path = case_path
    st.session_state.uploaded_name = uploaded_file.name
    st.session_state.original_case_text = case_path.read_text(encoding="utf-8")

    st.caption("Use anonymised procurement materials only.")

    st.markdown("### Step 1: Initial completeness check")
    st.write(
        "The system first extracts structured facts and checks whether important "
        "information is missing or unclear."
    )

    if st.button("🔎 Run Initial Completeness Check", type="primary"):
        with st.status("Running initial extraction...", expanded=True) as status:
            try:
                extracted_path = run_initial_extraction(case_path)
                extraction = json.loads(extracted_path.read_text(encoding="utf-8"))
                questions = generate_clarification_questions(extraction)

                st.session_state.extracted_path = extracted_path
                st.session_state.clarification_questions = questions
                st.session_state.stage = "clarification"

                status.update(label="Initial check complete!", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Initial check failed.", state="error")
                st.exception(e)

elif not uploaded_file and st.session_state.stage == "upload":
    st.info("Please upload a case file to begin.")


if st.session_state.stage == "clarification":
    questions = st.session_state.clarification_questions

    if questions:
        show_clarification_dialog(questions)
        st.info("The initial check found information that is missing or unclear.")
    else:
        st.success("No major missing information was identified. The case is ready for analysis.")
        if st.button("🚀 Analyse Case", type="primary", use_container_width=True):
            st.session_state.stage = "analysis_pending"
            st.rerun()


if st.session_state.stage == "supplementary_information":
    st.divider()
    st.subheader("➕ Add Information")
    st.write("Add any material that clarifies the gaps identified in the initial check.")

    additional_text = st.text_area(
        "Additional information",
        height=160,
        placeholder=(
            "For example: human oversight, legal basis, vendor responsibilities, "
            "or hosting / transfer information."
        ),
        key="additional_information_text",
    )

    supplementary_files = st.file_uploader(
        "Supporting materials (.txt) — optional",
        type=["txt"],
        accept_multiple_files=True,
        key="supplementary_materials",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Analyse With Added Information", type="primary", use_container_width=True):
            if not additional_text.strip() and not supplementary_files:
                st.warning("Please enter additional information or upload at least one supporting file.")
            else:
                supplementary_texts = {}
                if additional_text.strip():
                    supplementary_texts["user_additional_information.txt"] = additional_text.strip()

                for file in supplementary_files or []:
                    filename = safe_filename(file.name)
                    supplementary_texts[filename] = read_uploaded_text_file(file)

                questions = st.session_state.clarification_questions
                user_answers = {
                    question["question_id"]: "additional_material_uploaded"
                    for question in questions
                }

                combined_path = UPLOAD_DIR / f"{Path(st.session_state.case_path).stem}_combined.txt"

                write_combined_case_file(
                    output_path=combined_path,
                    original_case_text=st.session_state.original_case_text,
                    questions=questions,
                    user_answers=user_answers,
                    supplementary_texts=supplementary_texts,
                    direct_answers={},
                )

                st.session_state.case_path = combined_path
                st.session_state.stage = "analysis_pending"
                st.rerun()

    with col2:
        if st.button("Continue With Current Information", use_container_width=True):
            st.session_state.stage = "analysis_pending"
            st.rerun()


if st.session_state.stage == "analysis_pending":
    with st.status("Analysing the case...", expanded=True) as status:
        try:
            report_path = run_final_pipeline(Path(st.session_state.case_path))
            st.session_state.report_path = report_path
            st.session_state.stage = "final_report"
            status.update(label="Analysis complete!", state="complete")
            st.rerun()
        except Exception as e:
            status.update(label="Analysis failed.", state="error")
            st.exception(e)


if st.session_state.stage == "final_report":
    report_path = st.session_state.report_path

    if report_path:
        display_report(
            Path(report_path),
            uploaded_name=st.session_state.uploaded_name or "case.txt",
            case_path=Path(st.session_state.case_path),
        )

    st.divider()
    if st.button("🔄 Start New Case"):
        reset_session()
        st.rerun()
