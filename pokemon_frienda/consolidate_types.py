import csv
import os
import shutil

DB_CSV = "frienda_database_complete.csv"
BACKUP_CSV = "frienda_database_complete_type_backup.csv"

EXCLUDE_POKEMON = {"オーガポン", "テラパゴス"}

def parse_types(type_str):
    # Splits by common delimiters and returns a frozenset
    parts = [p.strip() for p in type_str.replace('、', ',').split(',') if p.strip()]
    return frozenset(parts)

def consolidate_types():
    shutil.copy2(DB_CSV, BACKUP_CSV)
    
    # Read data
    with open(DB_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        data = []
        for raw_row in reader:
            data.append({k: v for k, v in raw_row.items() if k is not None})
            
    # Group by name
    pokemon_types = {}
    for row in data:
        name = row.get("Name")
        poke_type = row.get("Type", "").strip()
        if not name or not poke_type:
            continue
            
        if name not in pokemon_types:
            pokemon_types[name] = []
        pokemon_types[name].append(poke_type)
        
    # Determine target type string for each Pokemon
    target_types_map = {}
    
    for name, type_strs in pokemon_types.items():
        if name in EXCLUDE_POKEMON:
            continue
            
        # Parse all type strings into frozensets
        type_sets = {}
        for ts in type_strs:
            parsed = parse_types(ts)
            if parsed not in type_sets:
                type_sets[parsed] = []
            type_sets[parsed].append(ts)
            
        # Find combination sets (length >= 2)
        combo_sets = [ps for ps in type_sets.keys() if len(ps) >= 2]
        
        if len(combo_sets) == 1:
            # Unambiguous 2-type combination exists. Let's find the most common raw string for it.
            target_set = combo_sets[0]
            raw_strs = type_sets[target_set]
            
            # Prefer a raw string that has a comma and space, like "はがね, フェアリー"
            best_raw = raw_strs[0]
            for rs in raw_strs:
                if ", " in rs:
                    best_raw = rs
                    break
            
            target_types_map[name] = best_raw
            
    # Apply consolidation
    updated_count = 0
    updated_details = []
    
    for row in data:
        name = row.get("Name")
        current_type = row.get("Type", "").strip()
        
        if name in target_types_map:
            target_type = target_types_map[name]
            
            # If current type is different from target, and it's not already the same combination
            if current_type != target_type:
                # Even if it's "フェアリー, はがね" vs "はがね, フェアリー", we overwrite it to standardize format
                row["Type"] = target_type
                updated_count += 1
                updated_details.append(f"{row['ID']} ({name}): '{current_type}' -> '{target_type}'")
                
    # Save
    with open(DB_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Consolidation complete. Updated {updated_count} records.")
    for detail in updated_details:
        print("  " + detail)
        
if __name__ == "__main__":
    consolidate_types()
