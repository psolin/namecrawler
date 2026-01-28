#!/usr/bin/env python3
"""
Update the database with newer SSA baby names data.

Instructions:
1. Download the latest data from: https://www.ssa.gov/oact/babynames/names.zip
2. Extract to a temporary directory
3. Run this script pointing to that directory

Usage:
    python update_ssa_data.py /path/to/extracted/names/

This will add any new years of data not already in the database.
"""

import sqlite3
import os
import argparse
from pathlib import Path
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'namecrawler' / 'data'
DB_PATH = DATA_DIR / 'names.sqlite'


def get_existing_years(cursor):
    """Get years already in the database."""
    cursor.execute('SELECT DISTINCT year FROM first ORDER BY year')
    return set(int(row[0]) for row in cursor.fetchall())


def parse_ssa_file(filepath):
    """Parse an SSA yobYYYY.txt file."""
    year_match = re.search(r'yob(\d{4})\.txt', filepath.name)
    if not year_match:
        return None, []

    year = int(year_match.group(1))
    records = []

    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 3:
                name, sex, count = parts
                records.append((name, sex, int(count), year))

    return year, records


def update_database(ssa_dir):
    """Update database with new SSA data."""
    ssa_path = Path(ssa_dir)

    if not ssa_path.exists():
        print(f"Error: Directory not found: {ssa_dir}")
        return False

    if not DB_PATH.exists():
        print(f"Error: Database not found: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        existing_years = get_existing_years(cursor)
        print(f"Existing years in database: {min(existing_years)}-{max(existing_years)}")

        # Find all yob*.txt files
        txt_files = sorted(ssa_path.glob('yob*.txt'))
        if not txt_files:
            print(f"No yob*.txt files found in {ssa_dir}")
            return False

        new_records = 0
        new_years = []

        for txt_file in txt_files:
            year, records = parse_ssa_file(txt_file)
            if year is None:
                continue

            if year in existing_years:
                continue

            print(f"Adding year {year}: {len(records)} names")
            new_years.append(year)

            for name, sex, count, yr in records:
                cursor.execute('''
                    INSERT OR REPLACE INTO first (first, sex, occurences, year)
                    VALUES (?, ?, ?, ?)
                ''', (name, sex, count, yr))
                new_records += 1

        if new_records > 0:
            conn.commit()
            print(f"\nAdded {new_records} records for years: {', '.join(map(str, sorted(new_years)))}")

            # Update indexes
            print("Updating indexes...")
            cursor.execute('ANALYZE')
            conn.commit()
        else:
            print("\nNo new years to add - database is up to date.")

        return True

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Update database with newer SSA baby names data',
        epilog='Download data from: https://www.ssa.gov/oact/babynames/names.zip'
    )
    parser.add_argument('ssa_dir', help='Directory containing extracted SSA yob*.txt files')
    args = parser.parse_args()

    return 0 if update_database(args.ssa_dir) else 1


if __name__ == '__main__':
    exit(main())
