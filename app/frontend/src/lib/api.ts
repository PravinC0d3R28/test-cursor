import axios from 'axios'

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

export async function fetchStyles() {
  const { data } = await axios.get(`${API_BASE}/styles`)
  return data.styles as Array<any>
}

export async function uploadMedia(file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axios.post(`${API_BASE}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as { media_id: string; path: string }
}

export async function transcribe(mediaId: string, language?: string) {
  const form = new FormData()
  if (language) form.append('language', language)
  const { data } = await axios.post(`${API_BASE}/transcribe/${mediaId}`, form)
  return data
}

export async function renderCaption(mediaId: string, styleId: string, resolution?: string, srtOnly?: boolean) {
  const payload = { media_id: mediaId, style_id: styleId, resolution, srt_only: !!srtOnly }
  const response = await fetch(`${API_BASE}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error('Render failed')
  const blob = await response.blob()
  return blob
}