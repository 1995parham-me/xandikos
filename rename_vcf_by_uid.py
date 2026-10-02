#!/usr/bin/env python

"""
Script to rename VCF files based on their UID field.
Ensures that each VCF filename matches the UID contained within the file.
"""

import sys
import argparse
from pathlib import Path


def extract_uid_from_vcf(filepath: Path) -> str | None:
    """
    Extract the UID from a VCF file.

    Args:
        filepath: Path to the VCF file

    Returns:
        str: The UID value, or None if not found
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("UID:"):
                    # Extract the UID value after 'UID:'
                    uid = line[4:].strip()
                    return uid
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

    return None


def rename_vcf_files(directory: str = ".", dry_run: bool = True) -> None:
    """
    Rename VCF files to match their internal UID.

    Args:
        directory: Directory containing VCF files
        dry_run: If True, only show what would be renamed without actually renaming
    """
    directory_path = Path(directory)
    vcf_files = list(directory_path.glob("*.vcf"))

    if not vcf_files:
        print(f"No VCF files found in {directory}")
        return

    print(f"Found {len(vcf_files)} VCF files")
    print()

    renamed_count = 0
    error_count = 0
    already_correct = 0

    for vcf_file in vcf_files:
        filename = vcf_file.name

        # Extract UID from file content
        uid = extract_uid_from_vcf(vcf_file)

        if uid is None:
            print(f"⚠️  WARNING: No UID found in {filename}")
            error_count += 1
            continue

        expected_filename = f"{uid}.vcf"

        if filename == expected_filename:
            already_correct += 1
            continue

        # Filename doesn't match UID
        new_filepath = vcf_file.parent / expected_filename

        # Check if target file already exists
        if new_filepath.exists():
            print(
                f"⚠️  WARNING: Cannot rename {filename} to {expected_filename} - target already exists"
            )
            error_count += 1
            continue

        if dry_run:
            print(f"Would rename: {filename} -> {expected_filename}")
        else:
            try:
                vcf_file.rename(new_filepath)
                print(f"✓ Renamed: {filename} -> {expected_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"⚠️  ERROR: Failed to rename {filename}: {e}")
                error_count += 1

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total VCF files: {len(vcf_files)}")
    print(f"Already correct: {already_correct}")

    if dry_run:
        print(f"Would rename: {len(vcf_files) - already_correct - error_count}")
    else:
        print(f"Successfully renamed: {renamed_count}")

    if error_count > 0:
        print(f"Errors/Warnings: {error_count}")

    if dry_run and (len(vcf_files) - already_correct - error_count) > 0:
        print()
        print("This was a DRY RUN. To actually rename files, run:")
        print(f"  python {sys.argv[0]} --apply")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rename VCF files to match their internal UID field",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be renamed):
  python rename_vcf_by_uid.py

  # Actually rename files:
  python rename_vcf_by_uid.py --apply

  # Specify a different directory:
  python rename_vcf_by_uid.py --directory /path/to/vcf/files --apply
        """,
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename files (default is dry run)",
    )

    parser.add_argument(
        "--directory",
        "-d",
        default=".",
        help="Directory containing VCF files (default: current directory)",
    )

    args = parser.parse_args()

    if not args.apply:
        print("DRY RUN MODE - No files will be renamed")
        print("Use --apply to actually rename files")
        print()

    rename_vcf_files(directory=args.directory, dry_run=not args.apply)


if __name__ == "__main__":
    main()
