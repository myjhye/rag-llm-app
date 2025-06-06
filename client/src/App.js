import { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "txt") return alert("Only .txt files are supported.");

    setFile(selectedFile);
    setUploading(true);
    setUploaded(false);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("session_id", sessionId);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploaded(true);
      } 
      else {
        alert(data.error || "Upload failed.");
      }
    } 
    catch {
      alert("Upload failed.");
    } 
    finally {
      setUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!question) return alert("Please enter a question.");
    setLoading(true);
    setAnswer("");

    const formData = new FormData();
    formData.append("question", question);
    formData.append("session_id", sessionId);

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setAnswer(data.answer || "No answer.");
    } 
    catch {
      alert("Failed to fetch answer.");
    } 
    finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 p-8 font-sans">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-6 text-center">
          📄 GPT Document Q&A
        </h1>

        {/* 파일 업로드 */}
        <div className="mb-4">
          <label className="block mb-1 font-medium">Upload a .txt file:</label>
          <input
            type="file"
            accept=".txt"
            onChange={handleFileChange}
            className="border border-gray-300 rounded px-3 py-2 w-full"
          />
          {uploading && <p className="text-sm text-blue-500 mt-1">Uploading...</p>}
          {uploaded && <p className="text-sm text-green-600 mt-1">Upload complete ✅</p>}
        </div>

        {/* 질문 입력 */}
        <div className="mb-4">
          <label className="block mb-1 font-medium">Ask a question:</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={!uploaded}
              className="border border-gray-300 rounded px-3 py-2 w-full disabled:opacity-50"
              placeholder={
                uploaded ? "e.g. What is LangChain?" : "Please upload a file first"
              }
            />
            <button
              onClick={handleAsk}
              disabled={!uploaded}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              Ask
            </button>
          </div>
        </div>

        {/* 응답 출력 */}
        {loading && <p className="text-sm text-gray-500">Thinking...</p>}
        {answer && (
          <div className="bg-gray-100 p-4 rounded border mt-4">
            <p className="text-sm text-gray-600 mb-1">GPT says:</p>
            <p className="font-medium whitespace-pre-line">{answer}</p>
          </div>
        )}
      </div>
    </div>
  );
}
