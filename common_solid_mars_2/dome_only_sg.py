import zipfile
from pathlib import Path

def extract_zip(zip_path, result_dir=None):

    zp = Path(zip_path)
    base_result = Path(result_dir) if result_dir else Path.cwd()
    if not zp.exists(): raise FileNotFoundError(f"ZIP파일을 찾을 수 없습니다. :{zp}")
    if not zp.is_file(): raise IsADirectoryError(f"경로 확인 필요! :{zp}")

    extract_dir = base_result / "mars_base"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zp, "r") as zf:
        names = zf.namelist()
        zf.extractall(extract_dir)
        print(f"-------압축해제완료-------->{extract_dir}")
        print("\n".join(names))
        print(f" 압축 해제된 파일 수: {len(names)}")

    return extract_dir
    
def load_csv(csv_path):
    csv_path = Path("mars_base/Mras_Base_Inventory_List.csv")

if __name__ == "__main__":
    extract_zip(Path.cwd() / "mars_base.zip")