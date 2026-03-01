import os
import sys
import shutil
import subprocess

DB_CSV = "frienda_database_complete.csv"
BACKUP_CSV = "archive/frienda_database_complete_rebuild_backup.csv"

def run_script(script_name):
    print(f"\n========================================")
    print(f"   実行中: {script_name}")
    print(f"========================================")
    try:
        # Run the script using Python and stream output
        result = subprocess.run([sys.executable, os.path.join("scripts", script_name)])
        return result.returncode == 0
    except Exception as e:
        print(f"Exception while running {script_name}: {e}")
        return False

def main():
    print("🌟 ポケモンフレンダ データベース更新パイプラインを開始します 🌟\n")
    
    rebuild = False
    if "--rebuild" in sys.argv:
        rebuild = True
        
    # Zero-downtime strategy: write to a temporary file during rebuild
    rebuild_csv = "data/frienda_database_rebuild.csv"
    
    if rebuild:
        print(f"⚠️  --rebuild フラグが指定されました。（ダウンタイムゼロ再構築モード）")
        print(f"   バックグラウンドで {rebuild_csv} に新しいデータを生成します...")
        os.environ["FRIENDA_OUTPUT_CSV"] = rebuild_csv
        
        # If the rebuild file doesn't exist yet, we start from scratch.
        # analyze_frienda.py will build it purely from frienda_database.csv
    else:
        # Normal mode: just update the live database
        os.environ["FRIENDA_OUTPUT_CSV"] = DB_CSV
    
    # 1. OCR解析の実行 (analyze_frienda.py)
    success_analyze = run_script("analyze_frienda.py")
    if not success_analyze:
        print("\n⚠️ 注意: analyze_frienda.py が途中で停止しました（APIの無料枠制限・エラーなど）。")
        print("   明日また同じコマンドを実行すれば、途中から再開します。")
        if rebuild:
             print(f"   ※ 今回はまだ途中なので、実際の {DB_CSV} は上書きされずに安全に保たれています！")
        return # Force stop the pipeline if we haven't finished the rebuild
        
    # 2. ユーザー報告パッチの適用 (apply_feedback.py)
    if os.path.exists("data/feedback.csv"):
        run_script("apply_feedback.py")
    else:
        print("\nℹ️ data/feedback.csv が見つからないため、ユーザー報告のパッチ適用をスキップします。")
        
    # 3. タイプの表記揺れ統一 (consolidate_types.py)
    run_script("consolidate_types.py")
    
    # 4. ピカチュウの例外対応 (revert_pikachu.py)
    if os.path.exists("scripts/revert_pikachu.py"):
        run_script("revert_pikachu.py")

    # 5. Swap the live database ONLY if rebuild finished successfully
    if rebuild:
        if os.path.exists(rebuild_csv):
            print(f"\n✅ 全レコードの再構築が完了しました！")
            print(f"   {DB_CSV} のバックアップを作成し、新しいデータに差し替えます...")
            if os.path.exists(DB_CSV):
                shutil.copy2(DB_CSV, BACKUP_CSV)
            shutil.move(rebuild_csv, DB_CSV)
        else:
            print("エラー: 再構築されたファイルが見つかりません。")
            return

    print("\n✅ 全ての処理が完了しました！データベース (frienda_database_complete.csv) は最新の状態です。")

if __name__ == "__main__":
    main()
