import json
import sys
import re
from pathlib import Path
from typing import Optional
from openai import OpenAI

client = OpenAI()


def extract_requirement_id(driver: str) -> Optional[str]:
    if not isinstance(driver, str):
        return None
    match = re.match(r"^(MR\d+)\b", driver.strip())
    return match.group(1) if match else None

def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_legal_references(
    requirement_mapping: dict,
    requirements_catalogue: list,
    decision_output: dict,
    triggered_only: bool = True,
    key_drivers_only: bool = True,
) -> list:
    req_map = {r["requirement_id"]: r for r in requirements_catalogue}
    refs = []

    items = requirement_mapping["requirement_assessments"]

    if triggered_only:
        items = [item for item in items if item.get("triggered")]

    selected_ids = None
    if key_drivers_only and decision_output:
        key_drivers = decision_output.get("key_drivers", [])
        driver_ids = []
        seen = set()
  
        for driver in key_drivers:
            req_id = extract_requirement_id(driver)
            if req_id and req_id not in seen:
                driver_ids.append(req_id)
                seen.add(req_id)     
        if driver_ids:
            selected_ids = set(driver_ids)
            

    if selected_ids is not None:
        item_map = {item["requirement_id"]: item for item in items}
        items = [item_map[rid] for rid in selected_ids if rid in item_map]

    for item in items:
        req_id = item["requirement_id"]
        source = req_map.get(req_id, {})
        
        primary_sources = source.get("primary_sources", [])
        supporting_sources = source.get("supporting_sources", [])

        if not primary_sources and not supporting_sources:
            continue
        refs.append({
            "requirement_id": req_id,
            "name": item["name"],
            "primary_sources": primary_sources,
            "supporting_sources": supporting_sources,
        })

    return refs

def build_report_input(extracted, requirement_mapping, decision_output, requirements_catalogue):
    legal_references = extract_legal_references(
        requirement_mapping,
        requirements_catalogue,
        decision_output=decision_output,
        triggered_only=True,
        key_drivers_only=True,
    )
    triggered_rules = [
        {
            "requirement_id": r["requirement_id"],
            "name": r["name"],
            "status": r["status"],
            "rationale": r["rationale"],
            "criticality": r["criticality"],
            "recommended_action": r["recommended_action"]
        }
        for r in requirement_mapping["requirement_assessments"]
        if r["triggered"]
    ]

    return {
        "structured_facts": extracted,
        "triggered_rules": triggered_rules,
        "legal_references": legal_references,
        "final_recommendation": decision_output
    }

def main():
    if len(sys.argv) < 5:
        print("Usage: python report_generation.py <extracted.json> <requirement_mapping.json> <decision_output.json> <requirements.json>")
        sys.exit(1)

    extracted_path = sys.argv[1]
    requirement_mapping_path = sys.argv[2]
    decision_output_path = sys.argv[3]
    requirements_path = sys.argv[4]

    extracted = load_json(extracted_path)
    requirement_mapping = load_json(requirement_mapping_path)
    decision_output = load_json(decision_output_path)
    requirements_catalogue = load_json(requirements_path)

    developer_prompt = load_text("report_generation_prompt.md")
    template_text = load_text("report_template.md")
    payload = build_report_input(extracted, requirement_mapping, decision_output, requirements_catalogue)

    user_prompt = (
        "Generate a preliminary compliance screening report based only on the structured inputs below.\n\n"
        "Use the report template below as the required output structure.\n"
        "Preserve the section headings from the template exactly.\n"
        "Replace all placeholder text in the template with case-specific content derived from the structured inputs.\n"
        "Do not invent facts, legal references, requirement outcomes, or recommendations.\n"
        "Do not change the provided risk level or recommended path.\n\n"
        "=== REPORT TEMPLATE ===\n"
        f"{template_text}\n\n"
        "=== STRUCTURED INPUTS ===\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {"role": "developer", "content": developer_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    report_text = response.output_text

    stem = Path(extracted_path).stem.replace("_extracted", "")
    output_path = Path(f"{stem}_report.md")
    output_path.write_text(report_text, encoding="utf-8")

    print(f"[OK] Report saved to: {output_path}")

if __name__ == "__main__":
    main()