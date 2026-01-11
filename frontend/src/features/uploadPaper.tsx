import { useRef } from 'react';


const UploadPaper = () => {


    const inputRef = useRef<HTMLInputElement | null>(null);

    async function storePDF(file: File) {
        const form = new FormData();
        form.append("file", file);

        const response = await fetch("http://localhost:8000/upload", {
            method: "POST",
            body: form
        });


        console.log('upload status', response.status);

    }
    return (
        <div>
            <button onClick={() => inputRef.current?.click()} >Upload Paper</button>
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
            }}/>
        </div>    
    );
}

export default UploadPaper;