import { useState, useEffect } from "react";
import { generatePreview } from "../api/client";
import type { AssetType } from "../api/types";

interface PreviewPaneProps {
  assetId: string | null;
  assetType: AssetType | null;
  objectUrl: string | null;
  duration: number | null | undefined;
  hexColor: string;
  similarity: number;
  blend: number;
}

export function PreviewPane({
  assetId,
  assetType,
  objectUrl,
  duration,
  hexColor,
  similarity,
  blend,
}: PreviewPaneProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [time, setTime] = useState(0.5);

  const isVideo = assetType === "video";

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleGenerate = async () => {
    if (!assetId || !hexColor || hexColor.length !== 6) {
      setError("アセットIDまたはキー色が設定されていません");
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const blob = await generatePreview(assetId, {
        hex: hexColor,
        similarity,
        blend,
        time: isVideo && duration ? Math.min(time, duration - 0.1) : undefined,
        max_width: 640,
      });

      // Revoke old URL
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "プレビュー生成に失敗しました");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="step-card">
      <h2>3. プレビュー</h2>

      <div className="preview-controls">
        {isVideo && duration && (
          <div className="setting-row">
            <label>タイムスタンプ (秒)</label>
            <input
              type="number"
              min="0"
              max={duration}
              step="0.1"
              value={time}
              onChange={(e) => setTime(parseFloat(e.target.value) || 0)}
              className="number-input"
            />
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={!assetId || !hexColor || generating}
        >
          {generating ? "生成中..." : "プレビュー生成"}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="preview-container">
        <div className="preview-columns">
          {objectUrl && (
            <div className="preview-column">
              <h4>{isVideo ? "元動画" : "元画像"}</h4>
              {isVideo ? (
                <video
                  src={objectUrl}
                  controls
                  muted
                  className="preview-video"
                />
              ) : (
                <img
                  src={objectUrl}
                  alt="Original"
                  className="preview-image"
                  style={{ maxWidth: "400px" }}
                />
              )}
            </div>
          )}

          <div className="preview-column">
            <h4>透過プレビュー</h4>
            {previewUrl ? (
              <div className="checkerboard-bg">
                <img src={previewUrl} alt="Preview" className="preview-image" />
              </div>
            ) : (
              <div className="preview-placeholder">
                プレビューを生成してください
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
