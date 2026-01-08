import { useRef, useState, useCallback } from "react";
import type { AssetResponse } from "../api/types";
import { uploadAsset } from "../api/client";

interface FileStepProps {
  asset: AssetResponse | null;
  onAssetUploaded: (asset: AssetResponse, objectUrl: string) => void;
}

export function FileStep({ asset, onAssetUploaded }: FileStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      setUploadProgress(0);

      try {
        const result = await uploadAsset(file, (progress) => {
          setUploadProgress(progress);
        });
        const objectUrl = URL.createObjectURL(file);
        onAssetUploaded(result, objectUrl);
      } catch (e) {
        setError(e instanceof Error ? e.message : "アップロードに失敗しました");
      } finally {
        setUploading(false);
      }
    },
    [onAssetUploaded]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileWithValidation(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileWithValidation(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB (should match backend)
  const ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
  const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/bmp', 'image/webp', 'image/gif'];
  const ALLOWED_TYPES = [...ALLOWED_VIDEO_TYPES, ...ALLOWED_IMAGE_TYPES];

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = Math.round(MAX_FILE_SIZE / (1024 * 1024));
      return `ファイルサイズが大きすぎます。最大${sizeMB}MBまでアップロード可能です。`;
    }

    // Check MIME type
    if (!ALLOWED_TYPES.includes(file.type) && file.type !== '') {
      return `サポートされていないファイル形式です。動画（MP4, MOV, AVI, MKV, WebM）または画像（PNG, JPG, BMP, WebP, GIF）を選択してください。`;
    }

    return null;
  };

  const handleFileWithValidation = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      handleFile(file);
    },
    [handleFile]
  );

  const isVideo = asset?.asset_type === "video";

  return (
    <div className="step-card">
      <h2>1. ファイルを選択</h2>

      {!asset && (
        <div
          className={`drop-zone ${dragOver ? "drag-over" : ""}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={handleKeyDown}
          tabIndex={0}
          role="button"
          aria-label="クリックまたはドラッグ&ドロップでファイルを選択"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*,image/*"
            onChange={handleFileChange}
            className="visually-hidden"
            aria-hidden="true"
          />
          {uploading ? (
            <div className="upload-progress">
              <p>アップロード中... {Math.round(uploadProgress * 100)}%</p>
              <div
                className="progress-bar"
                role="progressbar"
                aria-valuenow={Math.round(uploadProgress * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label="アップロード進捗"
              >
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress * 100}%` }}
                />
              </div>
            </div>
          ) : (
            <p>
              クリックまたはドラッグ&ドロップで
              <br />
              動画または画像ファイルを選択
            </p>
          )}
        </div>
      )}

      {error && <p className="error-message">{error}</p>}

      {asset && (
        <div className="asset-info">
          <p>
            <strong>ファイル名:</strong> {asset.filename}
          </p>
          <p>
            <strong>タイプ:</strong> {isVideo ? "動画" : "画像"}
          </p>
          <p>
            <strong>解像度:</strong> {asset.width} x {asset.height}
          </p>
          {isVideo && asset.duration != null && (
            <p>
              <strong>長さ:</strong> {asset.duration.toFixed(2)}秒
            </p>
          )}
          {isVideo && asset.fps != null && (
            <p>
              <strong>FPS:</strong> {asset.fps}
            </p>
          )}
          {isVideo && asset.has_audio != null && (
            <p>
              <strong>音声:</strong> {asset.has_audio ? "あり" : "なし"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
