import { useRef, useState } from 'react'

type Props = {
    onUploadComplete?: () => void
}

const UploadPaper = ({ onUploadComplete }: Props) => {
    const inputRef = useRef<HTMLInputElement | null>(null)
    const [busy, setBusy] = useState(false)

    async function storePDF(file: File) {
        setBusy(true)
        try {
            const form = new FormData()
            form.append('file', file)

            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: form,
            })

            console.log('upload status', response.status)
            if (response.ok) {
                onUploadComplete?.()
            }
        } finally {
            setBusy(false)
        }
    }

    return (
        <div>
            <button className="btn" disabled={busy} onClick={() => inputRef.current?.click()} >
                {busy ? "Uploading..." : "Upload Paper"}
            </button>
            <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                style={{ display: "none" }}
                onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    e.target.value = "";

                    storePDF(file);
                }} />
        </div>
    );
}

export default UploadPaper;