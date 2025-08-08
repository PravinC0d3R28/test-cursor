import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'OpenCaption Studio',
  description: 'Open-source online video captioning editor',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}