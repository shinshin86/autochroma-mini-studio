import { useState, useEffect } from "react";
import type { AssetResponse, ProbeResponse } from "./api/types";
import { probeFFmpeg } from "./api/client";
import { FileStep } from "./components/FileStep";
import { KeySettings } from "./components/KeySettings";
import { PreviewPane } from "./components/PreviewPane";
import { RenderPane } from "./components/RenderPane";

function App() {
  const [probeResult, setProbeResult] = useState<ProbeResponse | null>(null);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [asset, setAsset] = useState<AssetResponse | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  // Chromakey settings
  const [hexColor, setHexColor] = useState("");
  const [similarity, setSimilarity] = useState(0.1);
  const [blend, setBlend] = useState(0.05);
  const [crf, setCrf] = useState(24);
  const [includeAudio, setIncludeAudio] = useState(true);

  // Check ffmpeg on mount
  useEffect(() => {
    const checkProbe = async () => {
      try {
        const result = await probeFFmpeg();
        setProbeResult(result);
        if (!result.ok) {
          setProbeError(result.message || "ffmpegが見つかりません");
        }
      } catch (e) {
        setProbeError(
          e instanceof Error ? e.message : "バックエンドに接続できません"
        );
      }
    };
    checkProbe();
  }, []);

  const handleAssetUploaded = (newAsset: AssetResponse, newObjectUrl: string) => {
    // Cleanup old URL
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
    }
    setAsset(newAsset);
    setObjectUrl(newObjectUrl);
    // Reset chromakey settings
    setHexColor("");
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AutoChroma Mini Studio</h1>
        <p className="subtitle">動画・画像の背景を透過して書き出し</p>
      </header>

      {probeError && (
        <div className="warning-banner">
          <strong>警告:</strong> {probeError}
          <br />
          ffmpegとffprobeをインストールしてPATHに追加してください。
        </div>
      )}

      {probeResult?.ok && (
        <div className="info-banner">
          <small>
            {probeResult.ffmpeg} / {probeResult.ffprobe}
          </small>
        </div>
      )}

      <main className="main-content">
        <FileStep asset={asset} onAssetUploaded={handleAssetUploaded} />

        {asset && (
          <>
            <KeySettings
              assetId={asset.asset_id}
              assetType={asset.asset_type}
              hexColor={hexColor}
              similarity={similarity}
              blend={blend}
              crf={crf}
              includeAudio={includeAudio}
              onHexChange={setHexColor}
              onSimilarityChange={setSimilarity}
              onBlendChange={setBlend}
              onCrfChange={setCrf}
              onIncludeAudioChange={setIncludeAudio}
            />

            <PreviewPane
              assetId={asset.asset_id}
              assetType={asset.asset_type}
              objectUrl={objectUrl}
              duration={asset.duration}
              hexColor={hexColor}
              similarity={similarity}
              blend={blend}
            />

            <RenderPane
              assetId={asset.asset_id}
              assetType={asset.asset_type}
              hexColor={hexColor}
              similarity={similarity}
              blend={blend}
              crf={crf}
              includeAudio={includeAudio}
            />
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>AutoChroma Mini Studio - ローカル動画・画像透過ツール</p>
      </footer>
    </div>
  );
}

export default App;
