# AutoChroma Mini Studio

![Demo](./assets/demo.png)

動画・画像の背景色を自動推定し、ffmpegのchromakeyで透過(alpha)ファイルを書き出すローカルWebミニアプリ
- 動画 → WebM VP9 (透過動画)
- 画像 → PNG (透過画像)

[English README](./README.md)

## 必要要件

- **Python 3.11+**
- **Node.js 18+** (推奨: 20+)
- **uv** (Python パッケージマネージャー)
- **ffmpeg** と **ffprobe** がPATHで実行できること

### ffmpegのインストール

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
1. [ffmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード
2. 解凍して任意の場所に配置
3. 環境変数PATHにffmpegのbinフォルダを追加

## 起動手順

### ワンコマンド起動 (推奨)

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

依存関係のインストールとサーバー起動を自動で行います。

### 個別起動

**バックエンド:**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**フロントエンド:**
```bash
cd frontend
npm install
npm run dev
```

### 利用

ブラウザで http://localhost:5173 を開く

## テスト実行

**バックエンド:**
```bash
cd backend
uv run pytest
```

**フロントエンド:**
```bash
cd frontend
npm run test:run
```

## 使い方

1. **ファイルを選択**: ドラッグ&ドロップまたはクリックで動画・画像をアップロード
2. **背景色推定**: 「自動推定」ボタンで背景色を推定、または手動で指定
3. **パラメータ調整**: similarity, blend, CRFを調整（CRFは動画のみ）
4. **プレビュー確認**: プレビュー画像で透過結果を確認
5. **書き出し**: 「書き出し開始」で透過ファイルを生成
   - 動画 → WebM VP9 (透過動画)
   - 画像 → PNG (透過画像)
6. **ダウンロード**: 完了後にダウンロード

## トラブルシューティング

### `/api/probe` がok=falseを返す場合

ffmpegまたはffprobeがPATHに含まれていません。

```bash
# 確認方法
which ffmpeg
which ffprobe

# または
ffmpeg -version
ffprobe -version
```

インストールされていない場合は上記の手順でインストールしてください。

### Windowsでffmpegパスが通らない

1. システム環境変数の設定を開く
2. PATH変数にffmpegのbinフォルダのパスを追加
3. コマンドプロンプトを再起動

例: `C:\ffmpeg\bin` をPATHに追加

### 大きい動画でレンダリングに時間がかかる

これは正常な動作です。WebM VP9 + アルファのエンコードは計算量が多いため、動画の長さや解像度に応じて時間がかかります。進捗バーで処理状況を確認できます。

### CORSエラーが出る

バックエンドが起動していることを確認してください。フロントエンドはデフォルトで `http://localhost:8000` のバックエンドに接続します。

## プロジェクト構成

```
autochroma-mini-studio/
├── README.md         # 英語版README
├── README.ja.md      # 日本語版README
├── LICENSE
├── .gitignore
├── start.sh          # ワンコマンド起動 (macOS/Linux)
├── start.bat         # ワンコマンド起動 (Windows)
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── models.py
│   │   ├── storage.py
│   │   ├── ffmpeg_tools.py
│   │   └── jobs.py
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_ffmpeg_tools.py
│       ├── test_jobs.py
│       └── test_storage.py
└── frontend/
    ├── .env.example
    ├── package.json
    └── src/
        ├── test/
        │   └── setup.ts
        ├── api/
        │   ├── client.ts
        │   ├── client.test.ts
        │   └── types.ts
        ├── components/
        │   ├── FileStep.tsx
        │   ├── FileStep.test.tsx
        │   ├── KeySettings.tsx
        │   ├── KeySettings.test.tsx
        │   ├── PreviewPane.tsx
        │   ├── RenderPane.tsx
        │   └── LogPane.tsx
        ├── App.tsx
        ├── main.tsx
        └── index.css
```

## ライセンス

MIT License
