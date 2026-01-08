import type {
  ProbeResponse,
  AssetResponse,
  EstimateKeyResponse,
  PreviewRequest,
  RenderRequest,
  RenderResponse,
  JobResponse,
  CancelResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch {
      // ignore json parse error
    }
    throw new ApiError(response.status, message);
  }
  return response.json();
}

export async function probeFFmpeg(): Promise<ProbeResponse> {
  const response = await fetch(`${API_BASE}/api/probe`);
  return handleResponse<ProbeResponse>(response);
}

export async function uploadAsset(
  file: File,
  onProgress?: (progress: number) => void
): Promise<AssetResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/assets`);

    // Set timeout (5 minutes for large file uploads)
    xhr.timeout = 5 * 60 * 1000;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(event.loaded / event.total);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid JSON response"));
        }
      } else {
        let message = `HTTP ${xhr.status}`;
        try {
          const data = JSON.parse(xhr.responseText);
          message = data.detail || message;
        } catch {
          // ignore
        }
        reject(new ApiError(xhr.status, message));
      }
    };

    xhr.onerror = () => reject(new Error("ネットワークエラーが発生しました。接続を確認してください。"));

    xhr.ontimeout = () => reject(new Error("アップロードがタイムアウトしました。ファイルサイズが大きすぎるか、接続が遅い可能性があります。"));

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
}

export async function estimateKey(assetId: string): Promise<EstimateKeyResponse> {
  const response = await fetch(`${API_BASE}/api/assets/${assetId}/estimate-key`, {
    method: "POST",
  });
  return handleResponse<EstimateKeyResponse>(response);
}

export async function generatePreview(
  assetId: string,
  params: PreviewRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/assets/${assetId}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // ignore
    }
    throw new ApiError(response.status, message);
  }

  return response.blob();
}

export async function startRender(
  assetId: string,
  params: RenderRequest
): Promise<RenderResponse> {
  const response = await fetch(`${API_BASE}/api/assets/${assetId}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return handleResponse<RenderResponse>(response);
}

export async function getJobStatus(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  return handleResponse<JobResponse>(response);
}

export async function cancelJob(jobId: string): Promise<CancelResponse> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}/cancel`, {
    method: "POST",
  });
  return handleResponse<CancelResponse>(response);
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/download`;
}
