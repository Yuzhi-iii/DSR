import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str], step_name: str) -> None:
    print(f"\n=== Running {step_name} ===")
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{step_name} failed with exit code {result.returncode}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run_full_pipeline.py <case_file.txt> [requirements.json]")
        sys.exit(1)

    case_file = Path(sys.argv[1])
    if not case_file.exists():
        raise FileNotFoundError(f"Case file not found: {case_file}")

    requirements_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("requirements.json")
    if not requirements_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

    stem = case_file.stem

    extracted_file = Path(f"{stem}_extracted.json")
    requirement_mapping_file = Path(f"{stem}_requirement_mapping.json")
    decision_output_file = Path(f"{stem}_decision_output.json")
    report_file = Path(f"{stem}_report.md")

    python_exe = sys.executable

    # Step 1: extraction
    run_step(
        [python_exe, "full_schema_extraction.py", str(case_file)],
        "extraction"
    )

    if not extracted_file.exists():
        raise FileNotFoundError(f"Expected extraction output not found: {extracted_file}")

    # Step 2: requirement mapping + decision output
    run_step(
        [python_exe, "mapping_engine.py", str(extracted_file), "--requirements", str(requirements_file)],
        "mapping + decision"
    )

    if not requirement_mapping_file.exists():
        raise FileNotFoundError(f"Expected requirement mapping output not found: {requirement_mapping_file}")

    if not decision_output_file.exists():
        raise FileNotFoundError(f"Expected decision output not found: {decision_output_file}")

    # Step 3: report generation
    run_step(
        [
            python_exe,
            "report_generation.py",
            str(extracted_file),
            str(requirement_mapping_file),
            str(decision_output_file),
            str(requirements_file),
        ],
        "report generation"
    )

    if not report_file.exists():
        raise FileNotFoundError(f"Expected final report not found: {report_file}")

    print("\n=== Full pipeline completed successfully ===")
    print(f"[OK] Extracted JSON: {extracted_file}")
    print(f"[OK] Requirement mapping JSON: {requirement_mapping_file}")
    print(f"[OK] Decision output JSON: {decision_output_file}")
    print(f"[OK] Final report: {report_file}")


if __name__ == "__main__":
    main()