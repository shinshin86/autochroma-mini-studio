import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { KeySettings } from './KeySettings'
import * as client from '../api/client'

vi.mock('../api/client', () => ({
  estimateKey: vi.fn(),
}))

describe('KeySettings', () => {
  const defaultProps = {
    assetId: 'asset-123',
    assetType: 'video' as const,
    hexColor: '00FF00',
    similarity: 0.4,
    blend: 0.1,
    crf: 23,
    includeAudio: true,
    onHexChange: vi.fn(),
    onSimilarityChange: vi.fn(),
    onBlendChange: vi.fn(),
    onCrfChange: vi.fn(),
    onIncludeAudioChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('color input', () => {
    it('renders color picker with correct value', () => {
      render(<KeySettings {...defaultProps} />)

      const colorPicker = screen.getByLabelText('キー色を選択') as HTMLInputElement
      // Color input normalizes hex to lowercase
      expect(colorPicker).toHaveValue('#00ff00')
    })

    it('renders hex input with current value', () => {
      render(<KeySettings {...defaultProps} />)

      const hexInput = screen.getByPlaceholderText('RRGGBB') as HTMLInputElement
      expect(hexInput).toHaveValue('00FF00')
    })

    it('handles hex input changes', () => {
      render(<KeySettings {...defaultProps} />)

      const hexInput = screen.getByPlaceholderText('RRGGBB')
      fireEvent.change(hexInput, { target: { value: 'ff0000' } })

      expect(defaultProps.onHexChange).toHaveBeenCalledWith('FF0000')
    })

    it('handles hex input with # prefix', () => {
      render(<KeySettings {...defaultProps} />)

      const hexInput = screen.getByPlaceholderText('RRGGBB')
      fireEvent.change(hexInput, { target: { value: '#ff0000' } })

      expect(defaultProps.onHexChange).toHaveBeenCalledWith('FF0000')
    })

    it('strips invalid hex characters', () => {
      render(<KeySettings {...defaultProps} />)

      const hexInput = screen.getByPlaceholderText('RRGGBB')
      fireEvent.change(hexInput, { target: { value: 'GGHHII' } })

      // G, H, I are not valid hex chars, only preserves valid ones
      expect(defaultProps.onHexChange).toHaveBeenCalledWith('')
    })

    it('limits hex input to 6 characters', () => {
      render(<KeySettings {...defaultProps} />)

      const hexInput = screen.getByPlaceholderText('RRGGBB')
      fireEvent.change(hexInput, { target: { value: 'AABBCCDD' } })

      expect(defaultProps.onHexChange).toHaveBeenCalledWith('AABBCC')
    })

    it('handles color picker changes', () => {
      render(<KeySettings {...defaultProps} />)

      const colorPicker = screen.getByLabelText('キー色を選択')
      fireEvent.change(colorPicker, { target: { value: '#ff5500' } })

      expect(defaultProps.onHexChange).toHaveBeenCalledWith('FF5500')
    })
  })

  describe('auto estimate', () => {
    it('calls estimateKey on button click', async () => {
      vi.mocked(client.estimateKey).mockResolvedValue({
        hex: '#00CC00',
        rgb: { r: 0, g: 204, b: 0 },
        samples: 100,
      })

      render(<KeySettings {...defaultProps} />)

      const estimateButton = screen.getByText('自動推定')
      fireEvent.click(estimateButton)

      await waitFor(() => {
        expect(client.estimateKey).toHaveBeenCalledWith('asset-123')
        expect(defaultProps.onHexChange).toHaveBeenCalledWith('#00CC00')
      })
    })

    it('shows loading state during estimation', async () => {
      vi.mocked(client.estimateKey).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          hex: '#00CC00',
          rgb: { r: 0, g: 204, b: 0 },
          samples: 100,
        }), 100))
      )

      render(<KeySettings {...defaultProps} />)

      const estimateButton = screen.getByText('自動推定')
      fireEvent.click(estimateButton)

      expect(screen.getByText('推定中...')).toBeInTheDocument()
    })

    it('disables button when no assetId', () => {
      render(<KeySettings {...defaultProps} assetId={null} />)

      const estimateButton = screen.getByText('自動推定')
      expect(estimateButton).toBeDisabled()
    })

    it('shows error message on estimation failure', async () => {
      vi.mocked(client.estimateKey).mockRejectedValue(new Error('Estimation failed'))

      render(<KeySettings {...defaultProps} />)

      const estimateButton = screen.getByText('自動推定')
      fireEvent.click(estimateButton)

      await waitFor(() => {
        expect(screen.getByText('Estimation failed')).toBeInTheDocument()
      })
    })
  })

  describe('similarity slider', () => {
    it('renders with correct initial value', () => {
      render(<KeySettings {...defaultProps} />)

      const slider = screen.getByRole('slider', { name: '類似度' }) as HTMLInputElement
      expect(slider).toHaveValue('0.4')
    })

    it('handles slider changes', () => {
      render(<KeySettings {...defaultProps} />)

      const slider = screen.getByRole('slider', { name: '類似度' })
      fireEvent.change(slider, { target: { value: '0.3' } })

      expect(defaultProps.onSimilarityChange).toHaveBeenCalledWith(0.3)
    })

    it('handles number input changes', () => {
      render(<KeySettings {...defaultProps} />)

      const numberInput = screen.getByRole('spinbutton', { name: '類似度の数値入力' })
      fireEvent.change(numberInput, { target: { value: '0.25' } })

      expect(defaultProps.onSimilarityChange).toHaveBeenCalledWith(0.25)
    })
  })

  describe('blend slider', () => {
    it('renders with correct initial value', () => {
      render(<KeySettings {...defaultProps} />)

      const slider = screen.getByRole('slider', { name: 'ブレンド' }) as HTMLInputElement
      expect(slider).toHaveValue('0.1')
    })

    it('handles slider changes', () => {
      render(<KeySettings {...defaultProps} />)

      const slider = screen.getByRole('slider', { name: 'ブレンド' })
      fireEvent.change(slider, { target: { value: '0.2' } })

      expect(defaultProps.onBlendChange).toHaveBeenCalledWith(0.2)
    })
  })

  describe('video-specific settings', () => {
    it('shows CRF slider for video assets', () => {
      render(<KeySettings {...defaultProps} assetType="video" />)

      expect(screen.getByRole('slider', { name: 'CRF品質' })).toBeInTheDocument()
    })

    it('hides CRF slider for image assets', () => {
      render(<KeySettings {...defaultProps} assetType="image" />)

      expect(screen.queryByRole('slider', { name: 'CRF品質' })).not.toBeInTheDocument()
    })

    it('handles CRF slider changes', () => {
      render(<KeySettings {...defaultProps} />)

      const slider = screen.getByRole('slider', { name: 'CRF品質' })
      fireEvent.change(slider, { target: { value: '28' } })

      expect(defaultProps.onCrfChange).toHaveBeenCalledWith(28)
    })

    it('shows audio toggle for video assets', () => {
      render(<KeySettings {...defaultProps} assetType="video" />)

      expect(screen.getByRole('checkbox')).toBeInTheDocument()
    })

    it('hides audio toggle for image assets', () => {
      render(<KeySettings {...defaultProps} assetType="image" />)

      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    })

    it('handles audio toggle changes', () => {
      render(<KeySettings {...defaultProps} />)

      const checkbox = screen.getByRole('checkbox')
      fireEvent.click(checkbox)

      expect(defaultProps.onIncludeAudioChange).toHaveBeenCalledWith(false)
    })
  })

  describe('accessibility', () => {
    it('has proper labels for all inputs', () => {
      render(<KeySettings {...defaultProps} />)

      expect(screen.getByLabelText('キー色を選択')).toBeInTheDocument()
      expect(screen.getByLabelText('類似度')).toBeInTheDocument()
      expect(screen.getByLabelText('類似度の数値入力')).toBeInTheDocument()
      expect(screen.getByLabelText('ブレンド')).toBeInTheDocument()
      expect(screen.getByLabelText('ブレンドの数値入力')).toBeInTheDocument()
      expect(screen.getByLabelText('CRF品質')).toBeInTheDocument()
      expect(screen.getByLabelText('CRF品質の数値入力')).toBeInTheDocument()
    })
  })
})
