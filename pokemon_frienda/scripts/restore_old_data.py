import csv
import os

CURRENT_CSV = "frienda_database_complete.csv"
OLD_CSV = "archive/old_frienda.csv"
RESTORED_CSV = "archive/frienda_database_complete_restored.csv"

def restore_data():
    print("Loading old data...")
    old_data = {}
    try:
        with open(OLD_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for raw_row in reader:
                row = {k: v for k, v in raw_row.items() if k is not None}
                if row.get("ID"):
                    old_data[row["ID"]] = row
    except Exception as e:
        print(f"Error reading old CSV: {e}")
        return
        
    print(f"Loaded {len(old_data)} records from old commit.")
    
    print("\nApplying old data to current incomplete records...")
    current_rows = []
    restored_count = 0
    try:
        with open(CURRENT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames)
            for raw_row in reader:
                row = {k: v for k, v in raw_row.items() if k is not None}
                item_id = row.get("ID")
                
                # If the row has an ID and exists in the old data, let's restore missing fields
                if item_id and item_id in old_data:
                    old_row = old_data[item_id]
                    # Check if the current row lacks PokeEne (meaning it's the blank one we just added)
                    if not row.get("PokeEne") and old_row.get("PokeEne"):
                        # Restore all fields from old_row
                        for k in fieldnames:
                            if k in old_row and old_row[k]:
                                row[k] = old_row[k]
                        restored_count += 1
                        
                current_rows.append(row)
    except Exception as e:
         print(f"Error reading current CSV: {e}")
         return
         
    print(f"Restored data for {restored_count} records.")
    
    print(f"\nSaving to {RESTORED_CSV}...")
    with open(RESTORED_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(current_rows)
        
    print("Replacing current CSV with restored version...")
    os.replace(RESTORED_CSV, CURRENT_CSV)
    
    print("Done!")

if __name__ == "__main__":
    restore_data()
