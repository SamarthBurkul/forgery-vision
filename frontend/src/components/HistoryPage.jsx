import { useState, useEffect } from "react";

function VerdictBadge({ verdict }) {
  return verdict === "Tampered" ? (
    <span className="badge-tampered">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
      Tampered
    </span>
  ) : (
    <span className="badge-real">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
      Authentic
    </span>
  );
}

function ScoreBar({ value, color }) {
  return (
    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden mt-1">
      <div
        className={`h-full rounded-full ${color} transition-all duration-700`}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

function HistoryCard({ record }) {
  const {
    filename,
    timestamp,
    verdict,
    unified_score,
    ela_confidence,
    noise_score,
    edge_score,
    original_image_base64,
  } = record;

  const isTampered = verdict === "Tampered";
  const score      = Math.round(unified_score ?? 0);
  const date       = timestamp
    ? new Date(timestamp).toLocaleString()
    : "Unknown date";

  return (
    <div className={`card p-4 animate-fade-in flex flex-col sm:flex-row gap-4 ${
      isTampered ? "border-red-900/50" : "border-emerald-900/40"
    }`}>
      {/* Thumbnail */}
      <div className="w-full sm:w-28 sm:h-28 h-40 shrink-0 rounded-xl overflow-hidden bg-slate-900/50 border border-slate-800">
        {original_image_base64 ? (
          <img
            src={`data:image/jpeg;base64,${original_image_base64}`}
            alt="Thumbnail"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 text-xs text-center p-2">
            <span>🖼️</span>
            <span>No Image</span>
          </div>
        )}
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="min-w-0">
              <p className="font-semibold text-slate-100 truncate pr-2 text-sm">{filename || "Unnamed"}</p>
              <p className="text-[11px] text-slate-500">{date}</p>
            </div>
            <VerdictBadge verdict={verdict} />
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-3">
            {/* Score gauge (small) */}
            <div className="flex flex-col">
               <span className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">Forged Score</span>
               <div className={`text-2xl font-extrabold leading-none ${
                 score >= 60 ? "text-red-400" : score >= 35 ? "text-amber-400" : "text-emerald-400"
               }`}>
                 {score}
                 <span className="text-xs font-normal text-slate-500"> /100</span>
               </div>
            </div>
            
            {/* Breakdowns */}
            <div className="space-y-1.5 flex flex-col justify-center">
              <div>
                <div className="flex justify-between text-[9px] text-slate-400 leading-none">
                  <span>ELA</span>
                  <span>{((ela_confidence ?? 0) * 100).toFixed(1)}%</span>
                </div>
                <ScoreBar value={(ela_confidence ?? 0) * 100} color="bg-violet-500" />
              </div>
              <div>
                <div className="flex justify-between text-[9px] text-slate-400 leading-none">
                  <span>NOISE</span>
                  <span>{((noise_score ?? 0) * 100).toFixed(1)}%</span>
                </div>
                <ScoreBar value={(noise_score ?? 0) * 100} color="bg-blue-500" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HistoryPage({ api }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [filter,  setFilter]  = useState("All");

  useEffect(() => {
    (async () => {
      try {
        const res  = await fetch(`${api}/history`);
        if (!res.ok) throw new Error(`Server ${res.status}`);
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        setRecords(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [api]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Analysis History</h1>
          <p className="text-slate-500 text-sm mt-1">Last 20 analyses saved to MongoDB</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-slate-400 hover:text-white border border-slate-700
                     hover:border-slate-500 px-4 py-2 rounded-lg transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* States */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-5 h-40 shimmer" />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="card p-8 text-center space-y-2">
          <p className="text-red-400 font-medium">⚠ Could not load history</p>
          <p className="text-slate-500 text-sm">{error}</p>
          <p className="text-slate-600 text-xs">
            Make sure MongoDB is running and at least one analysis has been completed.
          </p>
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="card p-12 text-center space-y-3">
          <p className="text-4xl">📭</p>
          <p className="text-slate-300 font-semibold">No analyses yet</p>
          <p className="text-slate-500 text-sm">
            Run your first analysis and the results will appear here.
          </p>
        </div>
      )}

      {!loading && !error && records.length > 0 && (
        <>
          {/* Stats bar */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total",    val: records.length,
                color: "text-slate-200" },
              { label: "Tampered", val: records.filter(r => r.verdict === "Tampered").length,
                color: "text-red-400"   },
              { label: "Real",     val: records.filter(r => r.verdict !== "Tampered").length,
                color: "text-emerald-400" },
            ].map(({ label, val, color }) => (
              <div key={label} className="card p-4 text-center">
                <p className={`text-2xl font-bold ${color}`}>{val}</p>
                <p className="text-xs text-slate-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div className="flex justify-center gap-2 my-6">
            {["All", "Tampered", "Authentic"].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-5 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                  filter === f
                    ? "bg-violet-600 text-white shadow-lg shadow-violet-500/25"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Cards */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {records
              .filter(r => filter === "All" || (filter === "Authentic" && r.verdict !== "Tampered") || r.verdict === filter)
              .map((r) => (
                <HistoryCard key={r._id} record={r} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
