export interface ProbeResponse {
  ok: boolean;
  ffmpeg?: string;
  ffprobe?: string;
  message?: string;
}

export interface RGBColor {
  r: number;
  g: number;
  b: number;
}

export type AssetType = "video" | "image";

export interface AssetResponse {
  asset_id: string;
  filename: string;
  asset_type: AssetType;
  width: number;
  height: number;
  // Video-only fields (null for images)
  duration?: number | null;
  fps?: number | null;
  has_audio?: boolean | null;
}

export interface EstimateKeyResponse {
  hex: string;
  rgb: RGBColor;
  samples: number;
}

export interface PreviewRequest {
  hex: string;
  similarity: number;
  blend: number;
  time?: number | null; // Optional for images
  max_width: number;
}

export interface RenderRequest {
  hex: string;
  similarity: number;
  blend: number;
  crf?: number | null; // Video only
  include_audio?: boolean | null; // Video only
}

export interface RenderResponse {
  job_id: string;
}

export type JobStatus = "queued" | "running" | "done" | "error" | "canceled";

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  output_filename?: string;
  output_size_bytes?: number;
  last_log_lines: string[];
}

export interface CancelResponse {
  ok: boolean;
}

export interface ErrorResponse {
  detail: string;
}
