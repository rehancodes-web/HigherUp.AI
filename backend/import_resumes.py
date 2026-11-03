"""Bulk-add resumes to the talent pool from a folder (PDF, Word .docx or .txt).

    cd backend
    python import_resumes.py "C:\\path\\to\\resumes"                 # AI reads each resume, saves to SAP HANA
    python import_resumes.py "C:\\path\\to\\resumes" --json-out out.json   # only write a JSON file, no database

Uses the same .env as the API (HANA_* settings and OPENAI_API_KEY). Running it again replaces the profile
made from the same file name, so it is safe to repeat.
"""
import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from resume_summary import ResumeReadError, extract_resume_text, summarize_resume  # noqa: E402

SUPPORTED = {".pdf", ".docx", ".txt"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="folder containing the resumes")
    parser.add_argument("--json-out", help="write the profiles to this JSON file instead of saving to the database")
    args = parser.parse_args()

    files = sorted(p for p in Path(args.folder).iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
    if not files:
        print(f"No PDF, .docx or .txt files found in {args.folder}")
        return 1

    cursor = connection = None
    if not args.json_out:
        from main import get_db_connection  # imported here so --json-out works without database settings

        connection = get_db_connection()
        cursor = connection.cursor()
        from talent import save_profile

    profiles, failed = [], []
    for number, path in enumerate(files, 1):
        print(f"[{number}/{len(files)}] {path.name} ...", end=" ", flush=True)
        try:
            profile = summarize_resume(extract_resume_text(path.read_bytes(), path.name), path.name)
            if cursor is not None:
                profile = save_profile(cursor, profile)
                connection.commit()
            profiles.append(profile)
            print(f"{profile['name']} ({profile['mode']}, {len(profile['skills'])} skills)")
        except ResumeReadError as exc:
            failed.append((path.name, str(exc)))
            print(f"skipped: {exc}")
        except Exception as exc:  # keep going so one bad file doesn't stop the other 39
            if connection is not None:
                connection.rollback()
            failed.append((path.name, f"{type(exc).__name__}: {exc}"))
            print(f"FAILED: {type(exc).__name__}: {exc}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {len(profiles)} profiles to {args.json_out}")
    if connection is not None:
        connection.close()
    print(f"\nDone: {len(profiles)} added, {len(failed)} not added.")
    for name, reason in failed:
        print(f"  - {name}: {reason}")
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
