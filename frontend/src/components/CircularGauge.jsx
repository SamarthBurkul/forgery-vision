import { useEffect, useRef } from "react";

/**
 * Animated SVG circular gauge.
 * score: 0–100
 * verdict: "Real" | "Tampered"
 */
export default function CircularGauge({ score = 0, verdict = "Real" }) {
  const RADIUS      = 68;
  const STROKE_W    = 14;
  const CIRCUM      = 2 * Math.PI * RADIUS;
  const CENTER      = 100;

  // Colour zones
  const color =
    score >= 60 ? "#ef4444"   // red   — high forgery probability
    : score >= 35 ? "#f59e0b" // amber — uncertain
    : "#22c55e";              // green — likely authentic

  const bgColor    = "rgba(30,41,59,0.8)";
  const dashOffset = CIRCUM * (1 - score / 100);

  // Track-ring colour (dimmed version of main colour)
  const trackColor =
    score >= 60 ? "rgba(239,68,68,0.15)"
    : score >= 35 ? "rgba(245,158,11,0.15)"
    : "rgba(34,197,94,0.15)";

  // Animate on mount / change
  const ringRef = useRef(null);
  useEffect(() => {
    if (!ringRef.current) return;
    ringRef.current.style.strokeDashoffset = CIRCUM.toString();   // start fully hidden
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        ringRef.current.style.strokeDashoffset = dashOffset.toString();
      });
    });
  }, [score, dashOffset, CIRCUM]);

  return (
    <div className="flex flex-col items-center gap-4">
      <svg
        width="200" height="200"
        viewBox="0 0 200 200"
        className="overflow-visible"
        aria-label={`Forgery score ${score} out of 100`}
      >
        {/* Track ring */}
        <circle
          cx={CENTER} cy={CENTER} r={RADIUS}
          fill="none"
          stroke={trackColor}
          strokeWidth={STROKE_W}
        />

        {/* Score ring */}
        <circle
          ref={ringRef}
          cx={CENTER} cy={CENTER} r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE_W}
          strokeLinecap="round"
          strokeDasharray={CIRCUM}
          strokeDashoffset={CIRCUM}   /* animated via useEffect */
          transform={`rotate(-90 ${CENTER} ${CENTER})`}
          className="score-ring"
          style={{ filter: `drop-shadow(0 0 8px ${color}60)` }}
        />

        {/* Center content */}
        <text
          x={CENTER} y={CENTER - 10}
          textAnchor="middle"
          fill="white"
          fontSize="38"
          fontWeight="800"
          fontFamily="Inter, sans-serif"
        >
          {score}
        </text>
        <text
          x={CENTER} y={CENTER + 16}
          textAnchor="middle"
          fill="#64748b"
          fontSize="13"
          fontFamily="Inter, sans-serif"
        >
          / 100
        </text>
        <text
          x={CENTER} y={CENTER + 34}
          textAnchor="middle"
          fill="#94a3b8"
          fontSize="11"
          fontFamily="Inter, sans-serif"
        >
          forgery score
        </text>
      </svg>

      {/* Verdict badge */}
      <div className={verdict === "Tampered" ? "badge-tampered" : "badge-real"}>
        {verdict === "Tampered" ? (
          <>
            <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
            Tampered
          </>
        ) : (
          <>
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Authentic
          </>
        )}
      </div>

      {/* Score bands legend */}
      <div className="flex gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" /> 0–35 Likely real
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500" /> 35–60 Suspicious
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500" /> 60+ Tampered
        </span>
      </div>
    </div>
  );
}
