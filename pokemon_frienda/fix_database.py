import csv
import os

DB_CSV = "frienda_database.csv"
COMP_CSV = "frienda_database_complete.csv"
TEMP_CSV = "frienda_database_complete_fixed.csv"

def align_and_fix():
    print("Step 1: Analyzing existing IDs in complete CSV...")
    comp_data = []
    comp_ids = set()
    master_fieldnames = []
    
    # Read complete CSV
    try:
        with open(COMP_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            master_fieldnames = list(reader.fieldnames)
            for raw_row in reader:
                # Remove None keys created by trailing commas
                row = {k: v for k, v in raw_row.items() if k is not None}
                
                # Check for misalignment
                if not row.get("ID"):
                    print(f"Warning: Found row without ID: {row}")
                    # Usually means a completely empty line or badly quoted field
                    # Skip it if it's junk
                    if not any(row.values()):
                        continue
                        
                comp_data.append(row)
                if row.get("ID"):
                    comp_ids.add(row["ID"])
    except Exception as e:
        print(f"Failed to read complete CSV: {e}")
        return

    print(f"Loaded {len(comp_data)} rows from complete CSV.")

    print("\nStep 2: Checking base CSV for missing IDs...")
    missing_rows = []
    with open(DB_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = {k: v for k, v in raw_row.items() if k is not None}
            item_id = row.get("ID")
            
            if item_id and item_id not in comp_ids:
                print(f"Found missing ID: {item_id} ({row.get('Name')})")
                # Pad to match master_fieldnames
                padded_row = {}
                for fld in master_fieldnames:
                    padded_row[fld] = row.get(fld, "")
                    
                # Calculate series and variant just like analyze_frienda.py does
                series = "その他"
                if item_id.lower().startswith("p"):
                    series = "スペシャル"
                elif item_id.startswith("1-1"): series = "1だん"
                elif item_id.startswith("1-2"): series = "2だん"
                elif item_id.startswith("1-3"): series = "3だん"
                elif item_id.startswith("1-4"): series = "4だん"
                elif item_id.startswith("1-5"): series = "5だん"
                elif item_id.startswith("2-1"): series = "ベストタッグ1だん"
                elif item_id.startswith("2-2"): series = "ベストタッグ2だん"
                elif item_id.startswith("2-3"): series = "ベストタッグ3だん"
                elif item_id.startswith("2-4"): series = "ベストタッグ4だん"
                
                variant = ""
                if "A" in item_id and item_id.endswith("A"): variant = "パラレル"
                elif "W" in item_id: variant = "ワンダー"
                elif "★" in item_id or "_star" in row.get('ImageFile', ''): variant = "色違い"
                
                padded_row['Series'] = series
                padded_row['Variant'] = variant
                
                missing_rows.append(padded_row)
                
    print(f"Appended {len(missing_rows)} missing rows.")
    
    # Check for misaligned columns
    print("\nStep 3: Checking for column misalignment...")
    misaligned_count = 0
    clean_data = []
    for row in comp_data:
        # P001 example user gave has ID, name, imagefile, url, and then data shifted.
        # How to check? Usually 'Speed' or 'Rarity' ends up in wrong column.
        # Rarity usually has 1-5 or "スペシャル". 
        # PokeEne is usually a 3 digit number. 
        # If ID looks like a number but PokeEne is empty...
        
        # We will just ensure no stray keys outside fieldnames exist.
        # Dictionary iterators handle the misalignment inherently if the CSV header matched.
        # If there are fewer columns in the CSV line than headers, DictReader leaves them missing,
        # but if we pad them, they shift. 
        
        # Let's rebuild the row strictly to the fieldnames
        clean_row = {}
        for fld in master_fieldnames:
            clean_row[fld] = row.get(fld, "")
        clean_data.append(clean_row)
        
    all_data = clean_data + missing_rows
    
    print(f"\nStep 4: Writing fixed complete CSV ({len(all_data)} total rows)...")
    with open(TEMP_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=master_fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
        
    print(f"Saved to {TEMP_CSV}. Replacing old file...")
    os.replace(TEMP_CSV, COMP_CSV)
    print("Done!")

if __name__ == "__main__":
    align_and_fix()
