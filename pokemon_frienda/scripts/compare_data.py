import csv

OLD_CSV = "archive/old_frienda.csv"
CUR_CSV = "frienda_database_complete.csv"

old_data = {row["ID"]: row for row in csv.DictReader(open(OLD_CSV, "r")) if row.get("ID")}
cur_data = {row["ID"]: row for row in csv.DictReader(open(CUR_CSV, "r")) if row.get("ID")}

old_ids = set(old_data.keys())
cur_ids = set(cur_data.keys())

print(f"IDs only in OLD (deleted?): {len(old_ids - cur_ids)}")
if len(old_ids - cur_ids) > 0:
    print(f"Sample deleted IDs: {list(old_ids - cur_ids)[:10]}")
    
print(f"IDs only in CURRENT (new added?): {len(cur_ids - old_ids)}")
if len(cur_ids - old_ids) > 0:
    print(f"Sample new IDs: {list(cur_ids - old_ids)[:10]}")

diff_count = 0
for pid in sorted(list(old_ids.intersection(cur_ids))):
    old_row = old_data[pid]
    cur_row = cur_data[pid]
    diffs = []
    
    # Check all fields except those that might be naturally different or ignorable
    for k in old_row.keys():
        old_val = old_row.get(k, "")
        cur_val = cur_row.get(k, "")
        if old_val != cur_val:
            diffs.append(f"  {k}: '{old_val}' -> '{cur_val}'")
            
    if diffs:
        name = cur_row.get('Name', old_row.get('Name', 'Unknown'))
        print(f"[{pid} {name}] Differences:")
        for str_diff in diffs:
            print(str_diff)
        diff_count += 1

print(f"\nTotal records with modified data (compared to old commit): {diff_count}")
