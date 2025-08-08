type Segment = { start: number; end: number; text: string }

export default function CaptionEditor({ segments, onChange }: { segments: Segment[]; onChange: (segments: Segment[]) => void }) {
  function updateText(i: number, text: string) {
    const next = [...segments]
    next[i] = { ...next[i], text }
    onChange(next)
  }
  return (
    <div className="space-y-3 max-h-96 overflow-auto border rounded p-3 bg-white">
      {segments.map((s, i) => (
        <div key={i} className="flex gap-3 items-start">
          <div className="text-xs w-28 shrink-0 text-neutral-500">{s.start.toFixed(2)}s → {s.end.toFixed(2)}s</div>
          <input
            className="flex-1 border rounded px-2 py-1"
            value={s.text}
            onChange={(e) => updateText(i, e.target.value)}
          />
        </div>
      ))}
    </div>
  )
}