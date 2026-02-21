import csv
from collections import defaultdict

DB_CSV = "frienda_database_complete.csv"

def check_type_consistency():
    pokemon_types = defaultdict(list)
    
    with open(DB_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = {k: v for k, v in raw_row.items() if k is not None}
            name = row.get("Name")
            poke_type = row.get("Type", "").strip()
            item_id = row.get("ID")
            
            if name and poke_type:
                # Store the tuple of (Type, ID) for each Pokemon Name
                pokemon_types[name].append({"id": item_id, "type": poke_type})
                
    inconsistent_count = 0
    print("=== Pokémon with Inconsistent Types ===")
    
    for name, entries in pokemon_types.items():
        # Extract unique types for this Pokemon
        unique_types = set([e["type"] for e in entries])
        
        # If there's more than one unique type string, it's inconsistent
        if len(unique_types) > 1:
            inconsistent_count += 1
            print(f"\n[{name}] has {len(unique_types)} different type combinations:")
            
            # Group by type to show which IDs have which type
            type_groups = defaultdict(list)
            for e in entries:
                type_groups[e["type"]].append(e["id"])
                
            for t, ids in type_groups.items():
                print(f"  - Type: '{t}' (used by {len(ids)} IDs: {', '.join(ids[:5])}{'...' if len(ids) > 5 else ''})")
                
    print(f"\nTotal Pokémon with inconsistent types: {inconsistent_count}")

if __name__ == "__main__":
    check_type_consistency()
