#!/usr/bin/env python3
"""
Rebuild the names database with optimizations.

This script:
1. Uses proper numeric types instead of varchar (reduces size ~40%)
2. Adds indexes for faster lookups
3. Optionally aggregates first name data to reduce row count

Usage:
    python rebuild_database.py [--aggregate]

Data sources:
    - First names: Download from https://www.ssa.gov/oact/babynames/names.zip
    - Surnames: Already included (US Census 2010 via FiveThirtyEight)
"""

import sqlite3
import os
import argparse
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'namecrawler' / 'data'
OLD_DB = DATA_DIR / 'names.sqlite'
NEW_DB = DATA_DIR / 'names_optimized.sqlite'
SSA_TXT_DIR = DATA_DIR / 'social security - first' / 'txt'


def create_optimized_schema(cursor, aggregate=False):
    """Create tables with proper numeric types."""

    # Surnames table with proper types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS surnames (
            name TEXT PRIMARY KEY NOT NULL,
            rank INTEGER,
            count INTEGER,
            prop100k REAL,
            cum_prop100k REAL,
            pctwhite REAL,
            pctblack REAL,
            pctapi REAL,
            pctaian REAL,
            pct2prace REAL,
            pcthispanic REAL
        )
    ''')

    if aggregate:
        # Aggregated first names table (much smaller)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS first (
                first TEXT NOT NULL,
                sex TEXT NOT NULL,
                total_occurences INTEGER NOT NULL,
                peak_year INTEGER NOT NULL,
                peak_occurences INTEGER NOT NULL,
                first_year INTEGER,
                last_year INTEGER,
                PRIMARY KEY(first, sex)
            )
        ''')
    else:
        # Full first names table with proper types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS first (
                first TEXT NOT NULL,
                sex TEXT NOT NULL,
                occurences INTEGER NOT NULL,
                year INTEGER NOT NULL,
                PRIMARY KEY(first, sex, year)
            )
        ''')

    # Create indexes for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_first_name ON first(first)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_surnames_name ON surnames(name)')


def _safe_float(val):
    """Convert value to float, returning None for invalid/suppressed data."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if not val or val == '(S)':  # (S) means suppressed in Census data
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _safe_int(val):
    """Convert value to int, returning None for invalid data."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def migrate_surnames(old_cursor, new_cursor):
    """Migrate surnames with type conversion."""
    print("Migrating surnames...")

    old_cursor.execute('SELECT * FROM surnames')
    rows = old_cursor.fetchall()

    for row in rows:
        name = row[0]
        # Convert text to proper numeric types, handling special values
        rank = _safe_int(row[1])
        count = _safe_int(row[2])
        prop100k = _safe_float(row[3])
        cum_prop100k = _safe_float(row[4])
        pctwhite = _safe_float(row[5])
        pctblack = _safe_float(row[6])
        pctapi = _safe_float(row[7])
        pctaian = _safe_float(row[8])
        pct2prace = _safe_float(row[9])
        pcthispanic = _safe_float(row[10])

        new_cursor.execute('''
            INSERT OR REPLACE INTO surnames VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, rank, count, prop100k, cum_prop100k, pctwhite, pctblack,
              pctapi, pctaian, pct2prace, pcthispanic))

    print(f"  Migrated {len(rows)} surnames")


def migrate_first_names(old_cursor, new_cursor, aggregate=False):
    """Migrate first names with type conversion and optional aggregation."""
    print("Migrating first names...")

    if aggregate:
        # Aggregate by (first, sex) - compute summary statistics
        old_cursor.execute('''
            SELECT first, sex,
                   SUM(occurences) as total,
                   year, occurences
            FROM first
            GROUP BY first, sex
        ''')

        # Need to get peak year separately
        old_cursor.execute('''
            SELECT first, sex, SUM(occurences) as total_occ
            FROM first
            GROUP BY first, sex
        ''')
        name_totals = {(r[0], r[1]): r[2] for r in old_cursor.fetchall()}

        # Get peak year for each name
        old_cursor.execute('''
            SELECT first, sex, year, MAX(occurences) as peak_occ
            FROM first
            GROUP BY first, sex
        ''')
        peaks = {}
        for row in old_cursor.fetchall():
            peaks[(row[0], row[1])] = (int(row[2]), int(row[3]))

        # Get year ranges
        old_cursor.execute('''
            SELECT first, sex, MIN(year), MAX(year)
            FROM first
            GROUP BY first, sex
        ''')
        ranges = {(r[0], r[1]): (int(r[2]), int(r[3])) for r in old_cursor.fetchall()}

        count = 0
        for (first, sex), total in name_totals.items():
            peak_year, peak_occ = peaks.get((first, sex), (None, None))
            first_year, last_year = ranges.get((first, sex), (None, None))

            new_cursor.execute('''
                INSERT OR REPLACE INTO first VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (first, sex, int(total), peak_year, peak_occ, first_year, last_year))
            count += 1

        print(f"  Aggregated to {count} unique name-sex combinations")
    else:
        # Full migration with type conversion
        old_cursor.execute('SELECT first, sex, occurences, year FROM first')
        rows = old_cursor.fetchall()

        for row in rows:
            new_cursor.execute('''
                INSERT OR REPLACE INTO first VALUES (?, ?, ?, ?)
            ''', (row[0], row[1], int(row[2]), int(row[3])))

        print(f"  Migrated {len(rows)} first name records")


def rebuild_database(aggregate=False):
    """Rebuild the database with optimizations."""

    if not OLD_DB.exists():
        print(f"Error: Source database not found at {OLD_DB}")
        return False

    # Remove existing optimized DB if it exists
    if NEW_DB.exists():
        os.remove(NEW_DB)

    # Connect to both databases
    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    try:
        # Create optimized schema
        create_optimized_schema(new_cursor, aggregate)

        # Migrate data
        migrate_surnames(old_cursor, new_cursor)
        migrate_first_names(old_cursor, new_cursor, aggregate)

        # Commit and optimize
        new_conn.commit()

        # Run VACUUM to reclaim space
        print("Optimizing database...")
        new_cursor.execute('VACUUM')
        new_cursor.execute('ANALYZE')

        new_conn.commit()

        # Report sizes
        old_size = OLD_DB.stat().st_size / (1024 * 1024)
        new_size = NEW_DB.stat().st_size / (1024 * 1024)
        reduction = ((old_size - new_size) / old_size) * 100

        print(f"\nResults:")
        print(f"  Original size: {old_size:.1f} MB")
        print(f"  New size: {new_size:.1f} MB")
        print(f"  Reduction: {reduction:.1f}%")

        # Optionally replace original
        print(f"\nNew database saved to: {NEW_DB}")
        print("To replace the original, run:")
        print(f"  mv '{NEW_DB}' '{OLD_DB}'")

        return True

    finally:
        old_conn.close()
        new_conn.close()


def main():
    parser = argparse.ArgumentParser(description='Rebuild names database with optimizations')
    parser.add_argument('--aggregate', action='store_true',
                        help='Aggregate first names by name+sex (smaller but loses yearly data)')
    args = parser.parse_args()

    print("Rebuilding names database...")
    print(f"Mode: {'Aggregated' if args.aggregate else 'Full (with yearly data)'}")
    print()

    success = rebuild_database(aggregate=args.aggregate)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
