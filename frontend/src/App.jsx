import { useState } from "react";
import UploadZone   from "./components/UploadZone.jsx";
import ResultsPanel from "./components/ResultsPanel.jsx";
import LoadingSkeleton from "./components/LoadingSkeleton.jsx";
import HistoryPage  from "./components/HistoryPage.jsx";

const API = "http://localhost:5005";

export default function App() {
  const [page,      setPage]      = useState("home");   // "home" | "history"
  const [file,      setFile]      = useState(null);     // File object
  const [preview,   setPreview]   = useState(null);     // object URL
  const [loading,   setLoading]   = useState(false);
  const [results,   setResults]   = useState(null);
  const [error,     setError]     = useState(null);

  function handleImageSelect(f) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResults(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setResults(null);
    setError(null);

    const form = new FormData();
    form.append("image", file);

    try {
      const res  = await fetch(`${API}/analyze/full`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err.message || "Failed to reach the API. Is the Flask server running?");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setFile(null);
    setPreview(null);
    setResults(null);
    setError(null);
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-slate-800/70
                         bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <button
            onClick={() => { setPage("home"); handleReset(); }}
            className="flex items-center gap-2 group"
          >
            <span className="text-2xl">🔍</span>
            <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-blue-400
                             bg-clip-text text-transparent">
              ForensicAI
            </span>
          </button>

          <nav className="flex items-center gap-1">
            <NavBtn active={page === "home"}    onClick={() => { setPage("home"); }}>
              Analyze
            </NavBtn>
            <NavBtn active={page === "history"} onClick={() => setPage("history")}>
              History
            </NavBtn>
          </nav>
        </div>
      </header>

      {/* ── Main ─────────────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-10">
        {page === "history" ? (
          <HistoryPage api={API} />
        ) : (
          <>
            {/* Upload + controls */}
            {!results && !loading && (
              <section className="max-w-2xl mx-auto space-y-6 animate-fade-in">
                <div className="text-center space-y-2">
                  <h1 className="text-4xl font-extrabold tracking-tight
                                 bg-gradient-to-br from-white via-slate-200 to-slate-400
                                 bg-clip-text text-transparent">
                    Image Tampering Detection
                  </h1>
                  <p className="text-slate-400 text-base">
                    Upload an image — ELA · Noise Analysis · Edge Consistency · Score Fusion
                  </p>
                </div>

                <UploadZone
                  onImageSelect={handleImageSelect}
                  imagePreview={preview}
                />

                {error && (
                  <div className="p-4 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-sm">
                    ⚠ {error}
                  </div>
                )}

                {file && (
                  <div className="flex gap-3 justify-center">
                    <button className="btn-primary" onClick={handleAnalyze}>
                      Run Forensic Analysis →
                    </button>
                    <button
                      onClick={handleReset}
                      className="px-6 py-3 rounded-xl font-medium text-slate-400
                                 border border-slate-700 hover:border-slate-500
                                 hover:text-slate-200 transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                )}
              </section>
            )}

            {/* Loading skeleton */}
            {loading && <LoadingSkeleton />}

            {/* Results */}
            {results && !loading && (
              <section className="space-y-6 animate-fade-in">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <h2 className="text-xl font-bold text-slate-100">Analysis Results</h2>
                  <button
                    onClick={handleReset}
                    className="text-sm text-slate-400 hover:text-white transition-colors
                               border border-slate-700 px-4 py-2 rounded-lg hover:border-slate-500"
                  >
                    ← Analyze another image
                  </button>
                </div>
                <ResultsPanel results={results} preview={preview} />
              </section>
            )}
          </>
        )}
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/50 py-4 text-center
                         text-xs text-slate-600">
        ForensicAI · ELA + Noise + Edge Analysis · DenseNet121 Model
      </footer>
    </div>
  );
}

function NavBtn({ children, onClick, active }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? "bg-slate-800 text-white"
          : "text-slate-400 hover:text-white hover:bg-slate-800/50"
      }`}
    >
      {children}
    </button>
  );
}
