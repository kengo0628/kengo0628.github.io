
import csv
import sys
import shutil
from pathlib import Path

DB_FILE = "frienda_database_complete.csv"
FEEDBACK_FILE = "feedback.csv"  # The file provided by user
BACKUP_FILE = "frienda_database_complete_backup.csv"

def get_field_mapping(header_row):
    """Maps feedback CSV headers to DB CSV headers."""
    # Assuming GAS script saves: ID, Name, Field, Value, Date
    # Values for 'Field' are: HP, ATK, DEF, SP.ATK, SP.DEF, Speed, PokeEne, Type, MoveType, Rarity, Name
    pass

def apply_feedback():
    if not Path(FEEDBACK_FILE).exists():
        print(f"Error: Feedback file '{FEEDBACK_FILE}' not found.")
        print("Please download the Google Sheet as CSV and rename it to 'feedback.csv'.")
        return

    # Backup
    shutil.copy(DB_FILE, BACKUP_FILE)
    print(f"Backed up database to '{BACKUP_FILE}'.")

    # Load Data
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        data = {row['ID']: row for row in reader}

    # Load Feedback
    applied_count = 0
    with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Check headers
        if 'ID' not in reader.fieldnames or 'Field' not in reader.fieldnames or 'Value' not in reader.fieldnames:
             print("Error: feedback.csv must have 'ID', 'Field', and 'Value' columns.")
             return

        for row in reader:
            item_id = row['ID']
            field = row['Field']
            value = row['Value']

            if item_id in data:
                if field in fieldnames:
                    old_value = data[item_id][field]
                    if old_value != value:
                        data[item_id][field] = value
                        print(f"Updated {item_id}: {field} -> {value} (was {old_value})")
                        applied_count += 1
                else:
                    print(f"Warning: Field '{field}' not found in database for ID {item_id}.")
            else:
                print(f"Warning: ID '{item_id}' not found in database.")

    # Save
    if applied_count > 0:
        with open(DB_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data.values())
        print(f"Successfully applied {applied_count} changes.")
    else:
        print("No changes applied.")

if __name__ == "__main__":
    apply_feedback()
