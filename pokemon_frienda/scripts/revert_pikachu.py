import csv
import os
import shutil

DB_CSV = os.environ.get("FRIENDA_OUTPUT_CSV", "frienda_database_complete.csv")
BACKUP_CSV = "archive/frienda_database_complete_pikachu_backup.csv"

def revert_pikachu():
    with open(DB_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        data = list(reader)
        
    updated_count = 0
    for row in data:
        if row.get("Name") == "ピカチュウ":
            # If the script accidentally changed it to a combined type, revert it back to 'でんき'
            current_type = row.get("Type", "")
            if "ゴースト" in current_type or "," in current_type:
                row["Type"] = "でんき"
                updated_count += 1
                
    if updated_count > 0:
        with open(DB_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Reverted Type to 'でんき' for {updated_count} ピカチュウ records.")
    else:
        print("No ピカチュウ records needed reverting.")

if __name__ == "__main__":
    revert_pikachu()
