#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# 백엔드 설정: GUI 없이 파일로 저장 (macOS/VSCode 팝업 문제 회피)
import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

# ====== 사용자 환경 설정 (수정 가능) ======
KAGGLE_CONFIG_DIR = os.path.expanduser('~/.kaggle')  # kaggle.json 경로
DATASET_DIR = './data'  # 데이터셋 저장 경로
COMPETITION = 'spaceship-titanic'
# =======================================


def ensure_dataset_dir() -> None:
    """데이터셋 저장 폴더가 없으면 생성."""
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)
        print(f'📁 Created dataset directory: {DATASET_DIR}')


def dataset_exists() -> bool:
    """train.csv와 test.csv가 이미 존재하는지 확인."""
    train_file = os.path.join(DATASET_DIR, 'train.csv')
    test_file = os.path.join(DATASET_DIR, 'test.csv')
    return os.path.exists(train_file) and os.path.exists(test_file)


def _kaggle_cli_available() -> bool:
    """kaggle CLI 설치 여부 확인."""
    return shutil.which('kaggle') is not None


def download_dataset() -> None:
    """Kaggle에서 데이터셋 다운로드 및 압축 해제."""
    ensure_dataset_dir()

    if dataset_exists():
        print('✅ Dataset already exists. Skipping download.')
        return

    if not _kaggle_cli_available():
        print('❌ kaggle CLI가 설치되어 있지 않습니다. `pip install kaggle` 후 다시 시도하세요.')
        return

    try:
        print('📥 Downloading dataset from Kaggle...')
        subprocess.run(
            [
                'kaggle', 'competitions', 'download',
                '-c', COMPETITION,
                '-p', DATASET_DIR
            ],
            check=True,
            env={**os.environ, 'KAGGLE_CONFIG_DIR': KAGGLE_CONFIG_DIR}
        )

        # ZIP 압축 해제
        zip_path = os.path.join(DATASET_DIR, f'{COMPETITION}.zip')
        if os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DATASET_DIR)
            os.remove(zip_path)
            print('✅ Dataset extracted successfully.')
        else:
            print('⚠️ ZIP 파일을 찾지 못했습니다. 대회 참가(Join Competition) 여부를 확인하세요.')

    except subprocess.CalledProcessError as e:
        print('❌ Kaggle 다운로드 실패:', e)
        print('   - Kaggle 계정에서 해당 competition에 Join 했는지 확인하세요.')
        print('   - ~/.kaggle/kaggle.json 존재 및 권한(chmod 600) 확인하세요.')
    except Exception as e:  # 기타 예외
        print(f'❌ Error downloading dataset: {e}')


def configure_korean_font() -> None:
    """
    macOS/Windows/Linux에서 사용 가능한 한글 폰트를 우선순위로 설정한다.
    - 폰트가 있으면 addfont로 등록 후 rcParams에 지정
    - 마이너스 기호(−)가 네모로 깨지는 현상 방지
    - 벡터 저장 시 글자 깨짐 방지(pdf/svg 설정)
    """
    candidates = [
        # macOS 기본
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
        '/Library/Fonts/AppleGothic.ttf',
        # 사용자 설치 가능 폰트
        '/Library/Fonts/NanumGothic.ttf',
        '/Library/Fonts/NanumBarunGothic.ttf',
        str(Path.home() / 'Library/Fonts/NanumGothic.ttf'),
    ]

    chosen = None
    for p in candidates:
        if os.path.exists(p):
            try:
                font_manager.fontManager.addfont(p)
                font = font_manager.FontProperties(fname=p)
                matplotlib.rcParams['font.family'] = font.get_name()
                chosen = p
                break
            except Exception:
                pass

    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    matplotlib.rcParams['svg.fonttype'] = 'none'

    if chosen:
        print(f'📝 Using Korean font: {chosen}')
    else:
        print('⚠️ 한글 폰트를 경로에서 찾지 못했습니다. 시스템에 한글 TTF/TTC를 설치해 주세요.')


def load_and_merge(train_path: str, test_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """train.csv, test.csv 읽고 병합."""
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    merged = pd.concat([train, test], ignore_index=True)
    return train, test, merged


def save_merged_csv(df: pd.DataFrame, out_path: str) -> None:
    """병합된 데이터를 CSV로 저장 (엑셀 호환을 위해 utf-8-sig)."""
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'💾 Merged CSV saved: {out_path} (rows={len(df)})')


def show_data_info(df: pd.DataFrame) -> None:
    """전체 데이터 수량 출력."""
    print(f'전체 데이터 수량: {len(df)}')


def find_most_related_column(train_df: pd.DataFrame) -> Optional[str]:
    """
    Transported와 가장 관련성 높은 수치형 컬럼을 train에서 찾는다.
    (test에는 Transported가 없으므로 train만 사용)
    """
    if 'Transported' not in train_df.columns:
        print('⚠️ Transported 컬럼이 없습니다. (train.csv에만 있을 수 있음)')
        return None

    tmp = train_df.copy()
    for col in tmp.columns:
        if tmp[col].dtype == 'bool':
            tmp[col] = tmp[col].astype('int8')

    corr_series = tmp.corr(numeric_only=True)['Transported'].drop(labels=['Transported'], errors='ignore')
    if corr_series.empty:
        print('⚠️ 수치형 컬럼이 없어 상관계수를 계산할 수 없습니다.')
        return None

    related = corr_series.abs().idxmax()
    val = corr_series[related]
    print(f"🔎 Transported와 가장 관련된 항목: '{related}' (상관계수={val:.3f})")
    return related


def plot_age_groups(train_df: pd.DataFrame, outpath: str) -> None:
    """연령대별 Transported 비율 그래프(파일 저장)."""
    if 'Age' not in train_df.columns or 'Transported' not in train_df.columns:
        print('⚠️ Age 또는 Transported 컬럼이 없습니다.')
        return

    df = train_df[['Age', 'Transported']].dropna()
    bins = [0, 19, 29, 39, 49, 59, 69, 79, 120]
    labels = ['10대 이하', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상']
    df['AgeGroup'] = pd.cut(df['Age'], bins=bins, labels=labels, right=True, include_lowest=True)

    grouped = df.groupby('AgeGroup')['Transported'].mean()

    plt.figure()
    grouped.plot(kind='bar', edgecolor='black')
    plt.title('연령대별 Transported 비율')
    plt.ylabel('비율')
    plt.xlabel('연령대')
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
    print(f'🖼️ 연령대별 Transported 비율 그래프 저장: {outpath}')


def plot_destination_age_distribution(merged_df: pd.DataFrame, outpath: str) -> None:
    """보너스: Destination별 연령대 분포 시각화(파일 저장)."""
    if 'Age' not in merged_df.columns or 'Destination' not in merged_df.columns:
        print('⚠️ Age 또는 Destination 컬럼이 없습니다.')
        return

    df = merged_df[['Age', 'Destination']].dropna()
    bins = [0, 19, 29, 39, 49, 59, 69, 79, 120]
    labels = ['10대 이하', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상']
    df['AgeGroup'] = pd.cut(df['Age'], bins=bins, labels=labels, right=True, include_lowest=True)

    pivot = df.pivot_table(index='AgeGroup', columns='Destination',
                           values='Age', aggfunc='count').fillna(0)

    plt.figure()
    pivot.plot(kind='bar', stacked=True)
    plt.title('Destination별 연령대 분포')
    plt.ylabel('승객 수')
    plt.xlabel('연령대')
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
    print(f'🖼️ Destination별 연령대 분포 그래프 저장: {outpath}')


def main() -> None:
    # 폰트 설정(한글 깨짐 방지)
    configure_korean_font()

    # 1) 데이터 다운로드 (이미 있으면 스킵)
    download_dataset()

    # 2) 데이터 로드/병합
    train_path = os.path.join(DATASET_DIR, 'train.csv')
    test_path = os.path.join(DATASET_DIR, 'test.csv')

    if not (os.path.exists(train_path) and os.path.exists(test_path)):
        print('❌ train.csv 또는 test.csv를 찾지 못했습니다. 다운로드/경로를 확인하세요.')
        return

    train_df, test_df, merged_df = load_and_merge(train_path, test_path)

    # 병합본 저장
    merged_csv_path = os.path.join(DATASET_DIR, 'merged_spaceship_titanic.csv')
    save_merged_csv(merged_df, merged_csv_path)

    # 3) 전체 수량
    show_data_info(merged_df)

    # 4) Transported와 관련성 높은 항목 (train에서만)
    find_most_related_column(train_df)

    # 5) 연령대별 Transported 비율 (train 기준)
    plot_age_groups(train_df, os.path.join(DATASET_DIR, 'age_groups.png'))

    # 6) 보너스: Destination별 연령대 분포 (merged 기준)
    plot_destination_age_distribution(merged_df, os.path.join(DATASET_DIR, 'destination_age_distribution.png'))


if __name__ == '__main__':
    main()
