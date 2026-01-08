import { useState } from "react";
import { estimateKey } from "../api/client";
import type { AssetType } from "../api/types";

interface KeySettingsProps {
  assetId: string | null;
  assetType: AssetType | null;
  hexColor: string;
  similarity: number;
  blend: number;
  crf: number;
  includeAudio: boolean;
  onHexChange: (hex: string) => void;
  onSimilarityChange: (value: number) => void;
  onBlendChange: (value: number) => void;
  onCrfChange: (value: number) => void;
  onIncludeAudioChange: (value: boolean) => void;
}

export function KeySettings({
  assetId,
  assetType,
  hexColor,
  similarity,
  blend,
  crf,
  includeAudio,
  onHexChange,
  onSimilarityChange,
  onBlendChange,
  onCrfChange,
  onIncludeAudioChange,
}: KeySettingsProps) {
  const [estimating, setEstimating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isVideo = assetType === "video";

  const handleEstimate = async () => {
    if (!assetId) return;
    setEstimating(true);
    setError(null);

    try {
      const result = await estimateKey(assetId);
      onHexChange(result.hex);
    } catch (e) {
      setError(e instanceof Error ? e.message : "推定に失敗しました");
    } finally {
      setEstimating(false);
    }
  };

  const handleHexInput = (value: string) => {
    // Remove # if present
    let hex = value.replace(/^#/, "").toUpperCase();
    // Allow only hex characters
    hex = hex.replace(/[^0-9A-F]/gi, "");
    // Limit to 6 characters
    hex = hex.slice(0, 6);
    onHexChange(hex);
  };

  const handleColorPicker = (e: React.ChangeEvent<HTMLInputElement>) => {
    const hex = e.target.value.slice(1).toUpperCase();
    onHexChange(hex);
  };

  const displayHex = `#${hexColor || "000000"}`;

  return (
    <div className="step-card">
      <h2>2. 背景色とパラメータ設定</h2>

      <div className="settings-grid">
        <div className="setting-row">
          <label>キー色</label>
          <div className="color-input-group">
            <button
              className="btn btn-secondary"
              onClick={handleEstimate}
              disabled={!assetId || estimating}
            >
              {estimating ? "推定中..." : "自動推定"}
            </button>
            <input
              type="color"
              value={displayHex}
              onChange={handleColorPicker}
              className="color-picker"
              aria-label="キー色を選択"
            />
            <input
              type="text"
              value={hexColor}
              onChange={(e) => handleHexInput(e.target.value)}
              placeholder="RRGGBB"
              maxLength={6}
              className="hex-input"
            />
            <div
              className="color-swatch"
              style={{ backgroundColor: displayHex }}
            />
          </div>
        </div>

        {error && <p className="error-message">{error}</p>}

        <div className="setting-row">
          <label htmlFor="similarity-slider">Similarity (類似度)</label>
          <div className="slider-group">
            <input
              id="similarity-slider"
              type="range"
              min="0"
              max="0.5"
              step="0.01"
              value={similarity}
              onChange={(e) => onSimilarityChange(parseFloat(e.target.value))}
              aria-label="類似度"
            />
            <input
              type="number"
              min="0"
              max="0.5"
              step="0.01"
              value={similarity}
              onChange={(e) => onSimilarityChange(parseFloat(e.target.value))}
              className="number-input"
              aria-label="類似度の数値入力"
            />
          </div>
        </div>

        <div className="setting-row">
          <label htmlFor="blend-slider">Blend (ブレンド)</label>
          <div className="slider-group">
            <input
              id="blend-slider"
              type="range"
              min="0"
              max="0.5"
              step="0.01"
              value={blend}
              onChange={(e) => onBlendChange(parseFloat(e.target.value))}
              aria-label="ブレンド"
            />
            <input
              type="number"
              min="0"
              max="0.5"
              step="0.01"
              value={blend}
              onChange={(e) => onBlendChange(parseFloat(e.target.value))}
              className="number-input"
              aria-label="ブレンドの数値入力"
            />
          </div>
        </div>

        {isVideo && (
          <>
            <div className="setting-row">
              <label htmlFor="crf-slider">CRF (品質)</label>
              <div className="slider-group">
                <input
                  id="crf-slider"
                  type="range"
                  min="15"
                  max="40"
                  step="1"
                  value={crf}
                  onChange={(e) => onCrfChange(parseInt(e.target.value))}
                  aria-label="CRF品質"
                />
                <input
                  type="number"
                  min="15"
                  max="40"
                  step="1"
                  value={crf}
                  onChange={(e) => onCrfChange(parseInt(e.target.value))}
                  className="number-input"
                  aria-label="CRF品質の数値入力"
                />
              </div>
              <span className="hint">低いほど高品質・大ファイル</span>
            </div>

            <div className="setting-row">
              <span id="audio-toggle-label">音声を含める</span>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={includeAudio}
                  onChange={(e) => onIncludeAudioChange(e.target.checked)}
                  aria-labelledby="audio-toggle-label"
                />
                <span className="toggle-slider" aria-hidden="true"></span>
              </label>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
