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


# Page Configuration
st.set_page_config(
    page_title="AI Compliance Screener",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ AI Procurement Compliance Screening")
st.markdown("Automated preliminary assessment for AI-enabled health data procurement.")


UPLOAD_DIR = Path("temp_uploads")
REQUIREMENTS_PATH = "requirements.json"


# -----------------------------
# Utility functions
# -----------------------------

def safe_filename(name: str) -> str:
    """
    Convert uploaded filenames into boring safe filenames.
    Boring filenames are less likely to ruin the afternoon.
    """
    name = Path(name).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name or "uploaded_case.txt"


def extract_section(text: str, section_name: str) -> str:
    """
    Extract a Markdown section by ## heading.
    Captures content until the next ## heading or the end of the string.
    """
    pattern = rf"## {re.escape(section_name)}\n(.*?)(?=\n##\s|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No specific data found for this section."


def run_initial_extraction(case_path: Path) -> Path:
    """
    Run only the first extraction step.
    This creates <case_stem>_extracted.json.
    """
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
    """
    Run the complete pipeline:
    extraction -> mapping -> decision -> report.
    """
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


def display_report(report_path: Path, uploaded_name: str) -> None:
    """
    Display generated Markdown report in the Streamlit UI.
    """
    report_md = report_path.read_text(encoding="utf-8")

    st.divider()
    st.subheader("📝 Compliance Assessment Results")

    # Executive Summary
    st.info("### Executive Summary")
    summary_content = extract_section(report_md, "Executive Summary")
    st.markdown(summary_content)

    # Collapsible sections
    sections = [
        "Key Screening Concerns",
        "Priority Actions",
        "Structured Facts",
        "Key Missing Information",
        "Triggered Rules",
        "Legal References",
    ]

    for sec in sections:
        content = extract_section(report_md, sec)
        with st.expander(f"🔍 View {sec}"):
            st.markdown(content)

    # Final Recommendation
    st.markdown("---")
    st.success("### Final Recommendation")
    final_rec = extract_section(report_md, "Final Recommendation")
    st.markdown(final_rec)

    st.download_button(
        label="📥 Download Full Report (.md)",
        data=report_md,
        file_name=f"Compliance_Report_{uploaded_name.replace('.txt', '.md')}",
        mime="text/markdown",
    )


def reset_session() -> None:
    """
    Reset Streamlit session state for a new case.
    """
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
    """
    Initialise session state variables.
    """
    if "stage" not in st.session_state:
        st.session_state.stage = "upload"

    if "case_path" not in st.session_state:
        st.session_state.case_path = None

    if "uploaded_name" not in st.session_state:
        st.session_state.uploaded_name = ""

    if "original_case_text" not in st.session_state:
        st.session_state.original_case_text = ""

    if "extracted_path" not in st.session_state:
        st.session_state.extracted_path = None

    if "clarification_questions" not in st.session_state:
        st.session_state.clarification_questions = []

    if "report_path" not in st.session_state:
        st.session_state.report_path = None


def save_uploaded_case(uploaded_file) -> Path:
    """
    Save uploaded case file into temp_uploads.
    """
    UPLOAD_DIR.mkdir(exist_ok=True)

    safe_name = safe_filename(uploaded_file.name)
    case_path = UPLOAD_DIR / f"case_{safe_name}"

    case_path.write_bytes(uploaded_file.getbuffer())

    return case_path


def read_uploaded_text_file(uploaded_file) -> str:
    """
    Read a Streamlit uploaded text file safely as UTF-8.
    """
    return uploaded_file.getvalue().decode("utf-8")


# -----------------------------
# Sidebar
# -----------------------------

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
    st.caption("v1.5 | Clarification Round Added")


# -----------------------------
# Main flow
# -----------------------------

initialise_session_state()

uploaded_file = st.file_uploader(
    "Upload Case Description (.txt)",
    type=["txt"],
)

if uploaded_file and st.session_state.stage == "upload":
    case_path = save_uploaded_case(uploaded_file)

    st.session_state.case_path = case_path
    st.session_state.uploaded_name = uploaded_file.name
    st.session_state.original_case_text = case_path.read_text(encoding="utf-8")

    st.warning(
        "Before analysis, make sure the case text is anonymised and does not contain "
        "direct patient identifiers such as names, ID numbers, medical record numbers, "
        "phone numbers, addresses, or other identifying details."
    )

    st.markdown("### Step 1: Initial completeness check")
    st.write(
        "The system will first extract structured facts and identify whether additional "
        "materials may be useful before generating the final report."
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


# -----------------------------
# Clarification stage
# -----------------------------

if st.session_state.stage == "clarification":
    questions = st.session_state.clarification_questions

    st.divider()
    st.subheader("📌 Step 2: Additional Information Check")

    if not questions:
        st.success(
            "No major clarification questions were generated from the first-pass extraction."
        )

        st.write(
            "You can now generate the final preliminary compliance screening report "
            "using the original case description."
        )

        if st.button("🚀 Generate Final Report", type="primary"):
            with st.status("Running final pipeline...", expanded=True) as status:
                try:
                    report_path = run_final_pipeline(Path(st.session_state.case_path))
                    st.session_state.report_path = report_path
                    st.session_state.stage = "final_report"

                    status.update(label="Final report generated!", state="complete")
                    st.rerun()

                except Exception as e:
                    status.update(label="Final pipeline failed.", state="error")
                    st.exception(e)

    else:
        st.markdown(
            "The first-pass check found specific fields that are missing, unclear, "
            "partial, not provided, or otherwise unresolved. Please answer only the "
            "questions where you have additional information."
        )

        user_answers = {}
        direct_answers = {}
        needs_upload = False

        for question in questions:
            qid = question["question_id"]

            with st.container(border=True):
                st.markdown(f"### {question['topic']}")

                field_path = question.get("field_path", "")
                current_value = question.get("current_value", "")
                evidence_span = question.get("evidence_span", "")

                if field_path:
                    st.caption(f"Related field: `{field_path}`")

                st.write(f"**First-pass value:** `{current_value}`")

                if evidence_span:
                    with st.expander("View supporting excerpt from first-pass extraction"):
                        st.write(evidence_span)

                st.write(question["question"])

                material_prompt = question.get("material_prompt")
                if material_prompt:
                    st.caption(material_prompt)

                answer = st.radio(
                    label="How would you like to address this point?",
                    options=[
                        "direct_answer_provided",
                        "additional_material_uploaded",
                        "no_additional_information",
                    ],
                    format_func=lambda x: {
                        "direct_answer_provided": "I can answer this now",
                        "additional_material_uploaded": "I will upload supporting material",
                        "no_additional_information": "No additional information available",
                    }[x],
                    key=f"answer_{qid}",
                )

                user_answers[qid] = answer

                if answer == "direct_answer_provided":
                    direct_answers[qid] = st.text_area(
                        "Provide your clarification",
                        key=f"direct_answer_{qid}",
                        placeholder=(
                            "Write a short clarification based on the materials "
                            "or your knowledge of the case."
                        ),
                    )

                elif answer == "additional_material_uploaded":
                    needs_upload = True

        supplementary_files = []

        if needs_upload:
            st.divider()
            st.markdown("### Upload supplementary materials")
            st.write(
                "Upload relevant `.txt` materials for the questions marked as requiring "
                "supporting material. The system will combine these materials with the "
                "original case and your clarification responses."
            )

            supplementary_files = st.file_uploader(
                "Upload supplementary materials (.txt)",
                type=["txt"],
                accept_multiple_files=True,
            )

        st.divider()

        if st.button("🚀 Generate Final Report With Current Information", type="primary"):
            with st.status(
                "Preparing combined case and running final pipeline...",
                expanded=True,
            ) as status:
                try:
                    supplementary_texts = {}

                    for file in supplementary_files or []:
                        filename = safe_filename(file.name)
                        supplementary_texts[filename] = read_uploaded_text_file(file)

                    combined_path = (
                        UPLOAD_DIR
                        / f"{Path(st.session_state.case_path).stem}_combined.txt"
                    )

                    write_combined_case_file(
                        output_path=combined_path,
                        original_case_text=st.session_state.original_case_text,
                        questions=questions,
                        user_answers=user_answers,
                        supplementary_texts=supplementary_texts,
                        direct_answers=direct_answers,
                    )

                    report_path = run_final_pipeline(combined_path)

                    st.session_state.report_path = report_path
                    st.session_state.stage = "final_report"

                    status.update(label="Final report generated!", state="complete")
                    st.rerun()

                except Exception as e:
                    status.update(label="Final pipeline failed.", state="error")
                    st.exception(e)

# -----------------------------
# Final report stage
# -----------------------------

if st.session_state.stage == "final_report":
    report_path = st.session_state.report_path

    if report_path:
        display_report(
            Path(report_path),
            uploaded_name=st.session_state.uploaded_name or "case.txt",
        )

    st.divider()

    if st.button("🔄 Start New Case"):
        reset_session()
        st.rerun()