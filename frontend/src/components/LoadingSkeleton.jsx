/** Shimmer skeleton shown while /analyze/full is loading. */
export default function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-7 w-48 rounded-lg bg-slate-800 shimmer" />
        <div className="h-9 w-40 rounded-lg bg-slate-800 shimmer" />
      </div>

      {/* 4-panel grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Original Image", h: "h-52" },
          { label: "ELA Analysis",   h: "h-52" },
          { label: "Noise & Edge",   h: "h-52" },
          { label: "Forgery Score",  h: "h-52" },
        ].map(({ label, h }) => (
          <div key={label} className="card p-5 space-y-3">
            <div className="h-4 w-28 rounded bg-slate-800 shimmer" />
            <div className={`${h} rounded-xl bg-slate-800 shimmer`} />
            <div className="h-3 w-3/4 rounded bg-slate-800 shimmer" />
            <div className="h-3 w-1/2 rounded bg-slate-800 shimmer" />
          </div>
        ))}
      </div>

      {/* Spinner + message */}
      <div className="flex items-center justify-center gap-3 text-slate-400 text-sm py-4">
        <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"
                  strokeOpacity="0.25" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="#7c3aed" strokeWidth="3"
                strokeLinecap="round" />
        </svg>
        Running ELA · Noise · Edge analysis…
      </div>
    </div>
  );
}
