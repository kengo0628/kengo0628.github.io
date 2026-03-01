import csv
import json

class QuotaExceededError(Exception): pass

def simulate():
    # Simulate DB
    rows = [
        {'ID': '2-4-001', 'Name': 'Zygarde', 'PokeEne': ''},
        {'ID': '2-4-002', 'Name': 'Giratina', 'PokeEne': ''},
        {'ID': '2-4-003', 'Name': 'Regigigas', 'PokeEne': ''},
    ]

    master_fieldnames = ['ID', 'Name', 'PokeEne']

    completed_data = {}
    completed_ids = set()

    stop_processing = False
    updated_rows = []

    for row in rows:
        # Simulate initial setup
        for f in master_fieldnames:
            if f not in row:
                row[f] = ""
        
        item_id = row['ID']

        if stop_processing:
            row_to_add = {}
            if row['ID'] in completed_data:
                 row_to_add = completed_data[row['ID']]
            else:
                 row_to_add = row
            updated_rows.append(row_to_add)
            continue

        if item_id in completed_ids:
            merged_row = row.copy()
            merged_row.update(completed_data[item_id])
            updated_rows.append(merged_row)
            continue

        # Simulate analyze_image
        try:
            if item_id == '2-4-001':
                data = {'PokeEne': '362'} # Success
            elif item_id == '2-4-002':
                raise QuotaExceededError() # Fails
        except QuotaExceededError:
            print("Quota error!")
            stop_processing = True
            updated_rows.append(row)
            continue

        if data:
            def update_if_empty(key, val):
                if not row.get(key) and val:
                    row[key] = val
            update_if_empty('PokeEne', data.get('PokeEne', ''))
            
        updated_rows.append(row)

    print(json.dumps(updated_rows, indent=2))

simulate()
