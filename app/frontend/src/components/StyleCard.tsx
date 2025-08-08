export type CaptionStyle = {
  id: string
  label: string
  font: string
  primary_color: string
  emphasis_color: string
}

export default function StyleCard({ style, selected, onSelect }: { style: CaptionStyle; selected: boolean; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className={`border rounded p-3 text-left transition ${selected ? 'border-black shadow' : 'border-neutral-300 hover:border-neutral-500'}`}
    >
      <div className="text-sm text-neutral-500">{style.id}</div>
      <div className="text-lg font-semibold" style={{ fontFamily: style.font }}>{style.label}</div>
      <div className="mt-1 flex items-center gap-2">
        <span className="text-xs">Primary</span>
        <span className="w-4 h-4 rounded" style={{ backgroundColor: style.primary_color }} />
        <span className="text-xs">Emphasis</span>
        <span className="w-4 h-4 rounded" style={{ backgroundColor: style.emphasis_color }} />
      </div>
    </button>
  )
}