import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FileStep } from './FileStep'
import * as client from '../api/client'

vi.mock('../api/client', () => ({
  uploadAsset: vi.fn(),
}))

describe('FileStep', () => {
  const mockOnAssetUploaded = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:test-url'),
      revokeObjectURL: vi.fn(),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('initial state (no asset)', () => {
    it('renders drop zone when no asset is provided', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      expect(screen.getByRole('heading', { name: /ファイルを選択/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /クリックまたはドラッグ/ })).toBeInTheDocument()
    })

    it('has correct accessibility attributes', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })
      expect(dropZone).toHaveAttribute('tabIndex', '0')
    })

    it('triggers file input on Enter key', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(fileInput, 'click')

      fireEvent.keyDown(dropZone, { key: 'Enter' })

      expect(clickSpy).toHaveBeenCalled()
    })

    it('triggers file input on Space key', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(fileInput, 'click')

      fireEvent.keyDown(dropZone, { key: ' ' })

      expect(clickSpy).toHaveBeenCalled()
    })
  })

  describe('file validation', () => {
    it('rejects files larger than 500MB', async () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const largeFile = new File(['x'.repeat(100)], 'large.mp4', { type: 'video/mp4' })
      Object.defineProperty(largeFile, 'size', { value: 600 * 1024 * 1024 }) // 600MB

      fireEvent.change(fileInput, { target: { files: [largeFile] } })

      await waitFor(() => {
        expect(screen.getByText(/ファイルサイズが大きすぎます/)).toBeInTheDocument()
      })
      expect(client.uploadAsset).not.toHaveBeenCalled()
    })

    it('rejects unsupported file types', async () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const unsupportedFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' })

      fireEvent.change(fileInput, { target: { files: [unsupportedFile] } })

      await waitFor(() => {
        expect(screen.getByText(/サポートされていないファイル形式です/)).toBeInTheDocument()
      })
      expect(client.uploadAsset).not.toHaveBeenCalled()
    })

    it('accepts valid video files', async () => {
      const mockAsset = {
        asset_id: 'asset-123',
        filename: 'test.mp4',
        asset_type: 'video' as const,
        width: 1920,
        height: 1080,
        duration: 10.5,
        fps: 30,
        has_audio: true,
      }
      vi.mocked(client.uploadAsset).mockResolvedValue(mockAsset)

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const validFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      fireEvent.change(fileInput, { target: { files: [validFile] } })

      await waitFor(() => {
        expect(client.uploadAsset).toHaveBeenCalledWith(validFile, expect.any(Function))
      })
    })

    it('accepts valid image files', async () => {
      const mockAsset = {
        asset_id: 'asset-123',
        filename: 'test.png',
        asset_type: 'image' as const,
        width: 1920,
        height: 1080,
      }
      vi.mocked(client.uploadAsset).mockResolvedValue(mockAsset)

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const validFile = new File(['test'], 'test.png', { type: 'image/png' })

      fireEvent.change(fileInput, { target: { files: [validFile] } })

      await waitFor(() => {
        expect(client.uploadAsset).toHaveBeenCalledWith(validFile, expect.any(Function))
      })
    })
  })

  describe('upload process', () => {
    it('shows upload progress', async () => {
      let progressCallback: ((progress: number) => void) | undefined
      vi.mocked(client.uploadAsset).mockImplementation(async (_file, onProgress) => {
        progressCallback = onProgress
        return new Promise(() => {}) // Never resolves during test
      })

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const validFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      fireEvent.change(fileInput, { target: { files: [validFile] } })

      await waitFor(() => {
        expect(screen.getByText(/アップロード中/)).toBeInTheDocument()
      })

      // Simulate progress
      progressCallback?.(0.5)

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument()
      })
    })

    it('calls onAssetUploaded on successful upload', async () => {
      const mockAsset = {
        asset_id: 'asset-123',
        filename: 'test.mp4',
        asset_type: 'video' as const,
        width: 1920,
        height: 1080,
        duration: 10.5,
        fps: 30,
        has_audio: true,
      }
      vi.mocked(client.uploadAsset).mockResolvedValue(mockAsset)

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const validFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      fireEvent.change(fileInput, { target: { files: [validFile] } })

      await waitFor(() => {
        expect(mockOnAssetUploaded).toHaveBeenCalledWith(mockAsset, 'blob:test-url')
      })
    })

    it('displays error message on upload failure', async () => {
      vi.mocked(client.uploadAsset).mockRejectedValue(new Error('Upload failed'))

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const validFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      fireEvent.change(fileInput, { target: { files: [validFile] } })

      await waitFor(() => {
        expect(screen.getByText('Upload failed')).toBeInTheDocument()
      })
    })
  })

  describe('drag and drop', () => {
    it('shows drag-over state', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })

      fireEvent.dragOver(dropZone)

      expect(dropZone).toHaveClass('drag-over')
    })

    it('removes drag-over state on drag leave', () => {
      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })

      fireEvent.dragOver(dropZone)
      fireEvent.dragLeave(dropZone)

      expect(dropZone).not.toHaveClass('drag-over')
    })

    it('handles file drop', async () => {
      const mockAsset = {
        asset_id: 'asset-123',
        filename: 'test.mp4',
        asset_type: 'video' as const,
        width: 1920,
        height: 1080,
      }
      vi.mocked(client.uploadAsset).mockResolvedValue(mockAsset)

      render(<FileStep asset={null} onAssetUploaded={mockOnAssetUploaded} />)

      const dropZone = screen.getByRole('button', { name: /クリックまたはドラッグ/ })
      const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] },
      })

      await waitFor(() => {
        expect(client.uploadAsset).toHaveBeenCalled()
      })
    })
  })

  describe('asset display', () => {
    it('displays video asset info', () => {
      const videoAsset = {
        asset_id: 'asset-123',
        filename: 'test.mp4',
        asset_type: 'video' as const,
        width: 1920,
        height: 1080,
        duration: 10.5,
        fps: 30,
        has_audio: true,
      }

      render(<FileStep asset={videoAsset} onAssetUploaded={mockOnAssetUploaded} />)

      expect(screen.getByText('test.mp4')).toBeInTheDocument()
      expect(screen.getByText('動画')).toBeInTheDocument()
      expect(screen.getByText('1920 x 1080')).toBeInTheDocument()
      expect(screen.getByText('10.50秒')).toBeInTheDocument()
      expect(screen.getByText('30')).toBeInTheDocument()
      expect(screen.getByText('あり')).toBeInTheDocument()
    })

    it('displays image asset info', () => {
      const imageAsset = {
        asset_id: 'asset-123',
        filename: 'test.png',
        asset_type: 'image' as const,
        width: 1920,
        height: 1080,
      }

      render(<FileStep asset={imageAsset} onAssetUploaded={mockOnAssetUploaded} />)

      expect(screen.getByText('test.png')).toBeInTheDocument()
      expect(screen.getByText('画像')).toBeInTheDocument()
      expect(screen.getByText('1920 x 1080')).toBeInTheDocument()
      // Video-specific fields should not be present
      expect(screen.queryByText(/秒$/)).not.toBeInTheDocument()
    })

    it('hides drop zone when asset is present', () => {
      const asset = {
        asset_id: 'asset-123',
        filename: 'test.mp4',
        asset_type: 'video' as const,
        width: 1920,
        height: 1080,
      }

      render(<FileStep asset={asset} onAssetUploaded={mockOnAssetUploaded} />)

      expect(screen.queryByRole('button', { name: /クリックまたはドラッグ/ })).not.toBeInTheDocument()
    })
  })
})
