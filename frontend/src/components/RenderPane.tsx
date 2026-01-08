import { useState, useEffect, useRef } from "react";
import type { JobResponse, AssetType } from "../api/types";
import { startRender, getJobStatus, cancelJob, getDownloadUrl } from "../api/client";

interface RenderPaneProps {
  assetId: string | null;
  assetType: AssetType | null;
  hexColor: string;
  similarity: number;
  blend: number;
  crf: number;
  includeAudio: boolean;
}

export function RenderPane({
  assetId,
  assetType,
  hexColor,
  similarity,
  blend,
  crf,
  includeAudio,
}: RenderPaneProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const pollErrorCountRef = useRef(0);

  const isVideo = assetType === "video";

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    const MAX_POLL_ERRORS = 5;
    pollErrorCountRef.current = 0;
    setPollError(null);

    const poll = async () => {
      try {
        const status = await getJobStatus(jobId);
        setJob(status);
        pollErrorCountRef.current = 0; // Reset error count on success
        setPollError(null);

        if (status.status === "done" || status.status === "error" || status.status === "canceled") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      } catch (e) {
        pollErrorCountRef.current++;
        console.error("Failed to poll job status:", e);

        if (pollErrorCountRef.current >= MAX_POLL_ERRORS) {
          setPollError("ステータスの取得に繰り返し失敗しました。ネットワーク接続を確認してください。");
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      }
    };

    poll();
    pollRef.current = window.setInterval(poll, 1000);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, [jobId]);

  const handleStart = async () => {
    if (!assetId || !hexColor || hexColor.length !== 6) {
      setError("アセットまたはキー色が設定されていません");
      return;
    }

    setStarting(true);
    setError(null);
    setJob(null);

    try {
      const result = await startRender(assetId, {
        hex: hexColor,
        similarity,
        blend,
        crf: isVideo ? crf : undefined,
        include_audio: isVideo ? includeAudio : undefined,
      });
      setJobId(result.job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "レンダリング開始に失敗しました");
    } finally {
      setStarting(false);
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    try {
      await cancelJob(jobId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "キャンセルに失敗しました");
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isRunning = job?.status === "queued" || job?.status === "running";
  const isDone = job?.status === "done";
  const isError = job?.status === "error";
  const isCanceled = job?.status === "canceled";

  // Determine output format for display
  const outputFormat = isVideo ? "WebM (透過動画)" : "PNG (透過画像)";

  return (
    <div className="step-card">
      <h2>4. 書き出し</h2>

      <p className="hint" style={{ marginBottom: "16px" }}>
        出力形式: {outputFormat}
      </p>

      {!jobId && (
        <button
          className="btn btn-primary btn-large"
          onClick={handleStart}
          disabled={!assetId || !hexColor || starting}
        >
          {starting ? "開始中..." : "書き出し開始"}
        </button>
      )}

      {error && <p className="error-message">{error}</p>}

      {pollError && (
        <div className="error-info">
          <p className="error-message">{pollError}</p>
          <button className="btn btn-secondary" onClick={() => {
            pollErrorCountRef.current = 0;
            setPollError(null);
            // Restart polling
            if (jobId) {
              const poll = async () => {
                try {
                  const status = await getJobStatus(jobId);
                  setJob(status);
                  pollErrorCountRef.current = 0;
                  setPollError(null);
                } catch (e) {
                  pollErrorCountRef.current++;
                }
              };
              poll();
              pollRef.current = window.setInterval(poll, 1000);
            }
          }}>
            再試行
          </button>
        </div>
      )}

      {job && (
        <div className="job-status">
          <div className="status-row">
            <span className="status-label">ステータス:</span>
            <span className={`status-badge status-${job.status}`}>
              {job.status === "queued" && "待機中"}
              {job.status === "running" && (isVideo ? "レンダリング中" : "処理中")}
              {job.status === "done" && "完了"}
              {job.status === "error" && "エラー"}
              {job.status === "canceled" && "キャンセル"}
            </span>
          </div>

          {isRunning && isVideo && (
            <>
              <div
                className="progress-bar large"
                role="progressbar"
                aria-valuenow={Math.round(job.progress * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label="レンダリング進捗"
              >
                <div
                  className="progress-fill"
                  style={{ width: `${job.progress * 100}%` }}
                />
              </div>
              <p className="progress-text">{Math.round(job.progress * 100)}%</p>
              <button className="btn btn-danger" onClick={handleCancel}>
                キャンセル
              </button>
            </>
          )}

          {isRunning && !isVideo && (
            <p>処理中...</p>
          )}

          {isDone && (
            <div className="done-info">
              {job.output_size_bytes && (
                <p>ファイルサイズ: {formatBytes(job.output_size_bytes)}</p>
              )}
              <a
                href={getDownloadUrl(job.job_id)}
                className="btn btn-success btn-large"
                download
              >
                ダウンロード
              </a>
            </div>
          )}

          {isError && (
            <div className="error-info">
              <p className="error-message">{job.message}</p>
              <button className="btn btn-primary" onClick={handleStart}>
                再試行
              </button>
            </div>
          )}

          {isCanceled && (
            <div className="canceled-info">
              <p>処理がキャンセルされました</p>
              <button className="btn btn-primary" onClick={handleStart}>
                再開始
              </button>
            </div>
          )}

          {job.last_log_lines.length > 0 && (
            <div className="log-section">
              <h4>ログ</h4>
              <pre className="log-output">
                {job.last_log_lines.join("\n")}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
