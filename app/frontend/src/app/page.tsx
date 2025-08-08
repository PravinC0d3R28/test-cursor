"use client"

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { fetchStyles, renderCaption, transcribe, uploadMedia } from '@/lib/api'
import StyleCard, { type CaptionStyle } from '@/components/StyleCard'
import CaptionEditor from '@/components/CaptionEditor'

export default function Page() {
  const [file, setFile] = useState<File | null>(null)
  const [mediaId, setMediaId] = useState<string | null>(null)
  const [styles, setStyles] = useState<CaptionStyle[]>([])
  const [selectedStyleId, setSelectedStyleId] = useState<string | null>(null)
  const [segments, setSegments] = useState<any[]>([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isRendering, setIsRendering] = useState(false)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  useEffect(() => {
    fetchStyles().then((s) => {
      setStyles(s)
      if (s?.[0]) setSelectedStyleId(s[0].id)
    })
  }, [])

  const canTranscribe = !!file && !mediaId
  const canRender = !!mediaId && !!selectedStyleId

  async function handleUploadTranscribe() {
    if (!file) return
    setIsTranscribing(true)
    try {
      const up = await uploadMedia(file)
      setMediaId(up.media_id)
      const t = await transcribe(up.media_id)
      const segs = (t.transcript?.segments || []).map((s: any) => ({ start: s.start, end: s.end, text: s.text }))
      setSegments(segs)
    } finally {
      setIsTranscribing(false)
    }
  }

  async function handleRender(downloadSrt = false) {
    if (!mediaId || !selectedStyleId) return
    setIsRendering(true)
    try {
      const blob = await renderCaption(mediaId, selectedStyleId, undefined, downloadSrt)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = downloadSrt ? `${mediaId}.srt` : `${mediaId}_${selectedStyleId}.mp4`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setIsRendering(false)
    }
  }

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">OpenCaption Studio</h1>
      <p className="text-neutral-600">Upload a video, auto-generate captions, tweak the text, then render with trendy styles.</p>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-4">
          <div {...getRootProps()} className={`border-2 border-dashed rounded p-8 text-center bg-white ${isDragActive ? 'border-black' : 'border-neutral-300'}`}>
            <input {...getInputProps()} />
            {file ? (
              <div>
                <div className="font-semibold">{file.name}</div>
                <div className="text-sm text-neutral-500">{(file.size / (1024 * 1024)).toFixed(1)} MB</div>
              </div>
            ) : (
              <div>Drag & drop video here, or click to select</div>
            )}
          </div>

          <div className="flex gap-3">
            <button disabled={!canTranscribe || isTranscribing} onClick={handleUploadTranscribe} className="px-4 py-2 rounded bg-black text-white disabled:opacity-50">
              {isTranscribing ? 'Transcribing…' : 'Upload & Transcribe'}
            </button>
            <button disabled={!canRender || isRendering} onClick={() => handleRender(false)} className="px-4 py-2 rounded bg-emerald-600 text-white disabled:opacity-50">
              {isRendering ? 'Rendering…' : 'Render Burn-in MP4'}
            </button>
            <button disabled={!canRender || isRendering} onClick={() => handleRender(true)} className="px-4 py-2 rounded bg-neutral-800 text-white disabled:opacity-50">
              {isRendering ? 'Rendering…' : 'Download SRT'}
            </button>
          </div>

          {segments.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-semibold">Edit Captions</div>
              <CaptionEditor segments={segments} onChange={setSegments} />
              <div className="text-xs text-neutral-500">(Edits are local in this MVP. Click Render to burn current SRT; full two-way sync can be added.)</div>
            </div>
          )}
        </div>

        <aside className="space-y-3">
          <div className="text-sm font-semibold">Caption Styles</div>
          <div className="grid grid-cols-1 gap-3">
            {styles.map((s) => (
              <StyleCard key={s.id} style={s as any} selected={selectedStyleId === s.id} onSelect={() => setSelectedStyleId(s.id)} />
            ))}
          </div>
        </aside>
      </section>
    </main>
  )
}