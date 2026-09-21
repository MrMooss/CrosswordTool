import { useState } from 'react'

function App() {
  const [url, setUrl] = useState('')
  const [progress, setProgress] = useState(0)

  async function handleGenerate() {
    if (!url) return

    const response = await fetch(
      `/api/generate?url=${encodeURIComponent(url)}`,
      { method: 'POST' }
    )
    if (!response.ok) throw new Error('Failed to start crossword generation')

    const data = await response.json()
    let progress = await checkProgress(data.job_id)
    while (progress.status === 'pending') {
      await new Promise((resolve) => setTimeout(resolve, 500))
      progress = await checkProgress(data.job_id)
      setProgress(progress.percent)
    }

    if (progress.status === 'error') {
      throw new Error(progress.error ?? 'Failed to generate crossword')
    }

    await downloadPDF(data.job_id)
    setUrl('')
    setProgress(0)
  }

  return (
    <div className="App flex min-h-screen flex-col justify-center p-10">
      <div className="input-container">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter crossword URL"
        />
      </div>
      <div className="button-container w-full pt-2">
        <button
          type="button"
          className="rounded-lg bg-purple-400 w-full py-3 text-white hover:bg-purple-700"
          onClick={handleGenerate}
        >
          <div
            className="absolute left-0 top-0 h-full bg-purple-500/25 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />

          <span className="relative z-10 text-white">
            {progress > 0 ? `${progress}%` : "Generate Crossword"}
          </span>
        </button>
      </div>
    </div>  
  )

  async function checkProgress(jobId: string) {
    const response = await fetch(
      `/api/progress/${jobId}`
    )
    if (!response.ok) throw new Error('Failed to check crossword progress')
    const progress = await response.json()
    setProgress(progress.percent)
    return progress as { status: string; percent: number; error?: string }
  }

  async function downloadPDF(jobId: string) {
    const response = await fetch(
      `/api/download/${jobId}`
    )
    if (!response.ok) throw new Error('Failed to download crossword PDF')

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = 'crossword.pdf'
    document.body.appendChild(link)
    link.click()

    await new Promise((resolve) => setTimeout(resolve, 500))
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
  }

}

export default App