import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  probeFFmpeg,
  uploadAsset,
  estimateKey,
  generatePreview,
  startRender,
  getJobStatus,
  cancelJob,
  getDownloadUrl,
} from './client'

const API_BASE = 'http://localhost:8000'

describe('API Client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('probeFFmpeg', () => {
    it('should return probe response on success', async () => {
      const mockResponse = { ok: true, ffmpeg: '/usr/bin/ffmpeg', ffprobe: '/usr/bin/ffprobe' }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const result = await probeFFmpeg()

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/probe`)
      expect(result).toEqual(mockResponse)
    })

    it('should throw ApiError on failure', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'FFmpeg not found' }),
      } as Response)

      await expect(probeFFmpeg()).rejects.toThrow('FFmpeg not found')
    })

    it('should handle non-JSON error response', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Invalid JSON')),
      } as Response)

      await expect(probeFFmpeg()).rejects.toThrow('HTTP 500')
    })
  })

  describe('estimateKey', () => {
    it('should return estimate key response', async () => {
      const mockResponse = { hex: '#00ff00', rgb: { r: 0, g: 255, b: 0 }, samples: 100 }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const result = await estimateKey('test-asset-id')

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/assets/test-asset-id/estimate-key`, {
        method: 'POST',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('generatePreview', () => {
    it('should return blob on success', async () => {
      const mockBlob = new Blob(['test'], { type: 'image/png' })
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      } as Response)

      const params = { hex: '#00ff00', similarity: 0.4, blend: 0.1, max_width: 640 }
      const result = await generatePreview('test-asset-id', params)

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/assets/test-asset-id/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })
      expect(result).toBe(mockBlob)
    })

    it('should throw ApiError on failure', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Invalid parameters' }),
      } as Response)

      const params = { hex: '#00ff00', similarity: 0.4, blend: 0.1, max_width: 640 }
      await expect(generatePreview('test-asset-id', params)).rejects.toThrow('Invalid parameters')
    })
  })

  describe('startRender', () => {
    it('should return render response', async () => {
      const mockResponse = { job_id: 'job-123' }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const params = { hex: '#00ff00', similarity: 0.4, blend: 0.1 }
      const result = await startRender('test-asset-id', params)

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/assets/test-asset-id/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getJobStatus', () => {
    it('should return job response', async () => {
      const mockResponse = {
        job_id: 'job-123',
        status: 'running',
        progress: 0.5,
        created_at: '2024-01-01T00:00:00Z',
        last_log_lines: [],
      }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const result = await getJobStatus('job-123')

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/jobs/job-123`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('cancelJob', () => {
    it('should return cancel response', async () => {
      const mockResponse = { ok: true }
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const result = await cancelJob('job-123')

      expect(fetch).toHaveBeenCalledWith(`${API_BASE}/api/jobs/job-123/cancel`, {
        method: 'POST',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDownloadUrl', () => {
    it('should return correct download URL', () => {
      const result = getDownloadUrl('job-123')
      expect(result).toBe(`${API_BASE}/api/jobs/job-123/download`)
    })
  })
})

describe('uploadAsset', () => {
  let xhrInstance: {
    open: ReturnType<typeof vi.fn>
    send: ReturnType<typeof vi.fn>
    upload: { onprogress: ((event: ProgressEvent) => void) | null }
    onload: (() => void) | null
    onerror: (() => void) | null
    ontimeout: (() => void) | null
    timeout: number
    status: number
    responseText: string
  }
  let sendBehavior: () => void

  beforeEach(() => {
    sendBehavior = () => {}

    // Use a constructor function instead of arrow function
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const MockXMLHttpRequest = function (this: any) {
      this.open = vi.fn()
      this.upload = { onprogress: null }
      this.onload = null
      this.onerror = null
      this.ontimeout = null
      this.timeout = 0
      this.status = 200
      this.responseText = ''
      this.send = vi.fn(() => {
        sendBehavior()
      })
      xhrInstance = this
    } as unknown as typeof XMLHttpRequest

    vi.stubGlobal('XMLHttpRequest', MockXMLHttpRequest)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should upload file successfully', async () => {
    const mockResponse = {
      asset_id: 'asset-123',
      filename: 'test.mp4',
      asset_type: 'video',
      width: 1920,
      height: 1080,
    }

    sendBehavior = () => {
      xhrInstance.status = 200
      xhrInstance.responseText = JSON.stringify(mockResponse)
      xhrInstance.onload?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    const result = await uploadAsset(file)

    expect(xhrInstance.open).toHaveBeenCalledWith('POST', `${API_BASE}/api/assets`)
    expect(xhrInstance.timeout).toBe(5 * 60 * 1000)
    expect(result).toEqual(mockResponse)
  })

  it('should report upload progress', async () => {
    const mockResponse = { asset_id: 'asset-123', filename: 'test.mp4', asset_type: 'video', width: 1920, height: 1080 }
    const onProgress = vi.fn()

    sendBehavior = () => {
      const event = { lengthComputable: true, loaded: 50, total: 100 } as ProgressEvent
      xhrInstance.upload.onprogress?.(event)

      xhrInstance.status = 200
      xhrInstance.responseText = JSON.stringify(mockResponse)
      xhrInstance.onload?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    await uploadAsset(file, onProgress)

    expect(onProgress).toHaveBeenCalledWith(0.5)
  })

  it('should handle network error', async () => {
    sendBehavior = () => {
      xhrInstance.onerror?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    await expect(uploadAsset(file)).rejects.toThrow('ネットワークエラーが発生しました')
  })

  it('should handle timeout', async () => {
    sendBehavior = () => {
      xhrInstance.ontimeout?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    await expect(uploadAsset(file)).rejects.toThrow('アップロードがタイムアウトしました')
  })

  it('should handle HTTP error response', async () => {
    sendBehavior = () => {
      xhrInstance.status = 413
      xhrInstance.responseText = JSON.stringify({ detail: 'File too large' })
      xhrInstance.onload?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    await expect(uploadAsset(file)).rejects.toThrow('File too large')
  })

  it('should handle invalid JSON response', async () => {
    sendBehavior = () => {
      xhrInstance.status = 200
      xhrInstance.responseText = 'not json'
      xhrInstance.onload?.()
    }

    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    await expect(uploadAsset(file)).rejects.toThrow('Invalid JSON response')
  })
})
