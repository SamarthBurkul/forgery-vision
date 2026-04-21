import { useState } from "react";
import CircularGauge from "./CircularGauge.jsx";

/** Helper: convert base64 JPEG string to a data URL. */
const b64 = (str) => (str ? `data:image/jpeg;base64,${str}` : null);

/** Small score pill */
function ScorePill({ label, value, color }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
      <span className="text-xs text-slate-400">{label}</span>
      <span className={`text-sm font-semibold ${color}`}>
        {typeof value === "number" ? (value * 100).toFixed(1) + "%" : value}
      </span>
    </div>
  );
}

/** Panel card wrapper */
function Panel({ title, icon, children, className = "" }) {
  return (
    <div className={`card p-5 flex flex-col gap-3 animate-fade-in ${className}`}>
      <div className="panel-title flex items-center gap-2">
        {icon && <span>{icon}</span>}
        {title}
      </div>
      {children}
    </div>
  );
}

/** EXIF metadata table — shows up to 8 interesting fields */
const EXIF_KEYS_OF_INTEREST = [
  "Make", "Model", "DateTime", "DateTimeOriginal",
  "GPSInfo", "Software", "ImageWidth", "ImageLength",
  "ExifImageWidth", "ExifImageHeight",
];

function ExifTable({ exif }) {
  if (!exif || Object.keys(exif).length === 0) {
    return (
      <p className="text-xs text-slate-600 italic">No EXIF metadata found.</p>
    );
  }

  const entries = Object.entries(exif)
    .filter(([k]) => EXIF_KEYS_OF_INTEREST.some((ki) => k.includes(ki)))
    .slice(0, 8);

  if (entries.length === 0) {
    const fallback = Object.entries(exif).slice(0, 5);
    return (
      <table className="w-full text-xs">
        <tbody>
          {fallback.map(([k, v]) => (
            <tr key={k} className="border-b border-slate-800">
              <td className="py-1 pr-2 text-slate-500 font-medium">{k}</td>
              <td className="py-1 text-slate-300 break-all">{String(v).slice(0, 40)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <table className="w-full text-xs">
      <tbody>
        {entries.map(([k, v]) => (
          <tr key={k} className="border-b border-slate-800">
            <td className="py-1 pr-2 text-slate-500 font-medium whitespace-nowrap">
              {k}
            </td>
            <td className="py-1 text-slate-300 break-all">
              {String(v).slice(0, 45)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Sub-section label inside a panel */
function SubLabel({ children }) {
  return (
    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600 mt-1">
      {children}
    </p>
  );
}

export default function ResultsPanel({ results, preview }) {
  const {
    verdict,
    unified_score,
    ela_confidence,
    noise_score,
    edge_score,
    original_image_base64,
    ela_image_base64,
    gradcam_base64,
    annotated_image_base64,
    noise_image_base64,
    edge_image_base64,
    copy_move,
    exif,
    filename,
    analysis_id,
  } = results;

  const [elaTab, setElaTab] = useState("ela");

  const isTampered = verdict === "Tampered";
  const scoreInt   = Math.round(unified_score ?? 0);

  return (
    <>
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

      {/* ── Panel 1 — Original + EXIF ──────────────────────────────────── */}
      <Panel title="Original Image" icon="🖼">
        <div className="relative">
          <img
            src={b64(annotated_image_base64) ?? b64(original_image_base64) ?? preview}
            alt="Uploaded original"
            className="w-full rounded-xl object-contain max-h-52 bg-slate-950"
          />
          {annotated_image_base64 && (
            <div className="absolute bottom-2 left-2 bg-red-500/80 text-white
                            text-[10px] px-2 py-0.5 rounded-md backdrop-blur-sm font-medium">
              Suspected tampered region highlighted
            </div>
          )}
        </div>
        {filename && (
          <p className="text-[11px] text-slate-500 truncate">{filename}</p>
        )}
        <SubLabel>EXIF Metadata</SubLabel>
        <ExifTable exif={exif} />
      </Panel>

      {/* ── Panel 2 — ELA + Grad-CAM (tabbed) ───────────────────────── */}
      <Panel title="ELA Analysis" icon="⚡">
        {/* Tab switcher */}
        <div className="flex gap-1 mb-2">
          <button
            onClick={() => setElaTab("ela")}
            className={`px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              elaTab === "ela"
                ? "bg-violet-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            ELA Heatmap (raw)
          </button>
          {gradcam_base64 && (
            <button
              onClick={() => setElaTab("gradcam")}
              className={`px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                elaTab === "gradcam"
                  ? "bg-violet-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              Grad-CAM
            </button>
          )}
        </div>

        {/* Active tab content */}
        {elaTab === "ela" ? (
          <>
            <div className="relative">
              <img
                src={b64(isTampered && annotated_image_base64 ? annotated_image_base64 : ela_image_base64)}
                alt="ELA heatmap"
                className="w-full rounded-xl object-contain max-h-52 bg-slate-950"
              />
              {isTampered && annotated_image_base64 && (
                <div className="absolute top-2 left-2 bg-red-500/80 text-white
                                text-[10px] px-2 py-0.5 rounded-md backdrop-blur-sm font-medium">
                  ⬛ Region detected
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <img
              src={b64(gradcam_base64)}
              alt="Grad-CAM visualization"
              className="w-full rounded-xl object-contain max-h-52 bg-slate-950"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              Grad-CAM: regions the neural network focused on when classifying
            </p>
          </>
        )}

        <ScorePill
          label="ELA Tampered Probability"
          value={ela_confidence}
          color={ela_confidence > 0.05 ? "text-red-400" : "text-emerald-400"}
        />
        <p className="text-[11px] text-slate-600">
          Decision threshold: 0.05 (bias-corrected)
        </p>
      </Panel>

      {/* ── Panel 3 — Noise + Edge Maps ────────────────────────────────── */}
      <Panel title="Noise &amp; Edge Maps" icon="🔬">
        <SubLabel>Noise Inconsistency Map (HOT)</SubLabel>
        <img
          src={b64(noise_image_base64)}
          alt="Noise map"
          className="w-full rounded-xl object-contain max-h-28 bg-slate-950"
        />
        <ScorePill
          label="Noise Inconsistency"
          value={noise_score}
          color={noise_score > 0.5 ? "text-red-400" : "text-emerald-400"}
        />

        <SubLabel>Edge Gradient Consistency Map (JET)</SubLabel>
        <img
          src={b64(edge_image_base64)}
          alt="Edge map"
          className="w-full rounded-xl object-contain max-h-28 bg-slate-950"
        />
        <ScorePill
          label="Edge Inconsistency"
          value={edge_score}
          color={edge_score > 0.6 ? "text-red-400" : "text-slate-300"}
        />

        <p className="text-[11px] text-slate-600 pt-1">
          HOT = Laplacian variance · JET = Circular gradient variance + Canny edges
        </p>
      </Panel>

      {/* ── Panel 4 — Score Gauge + Verdict ───────────────────────────── */}
      <Panel title="Forgery Score" icon="🎯">
        <div className="flex-1 flex flex-col items-center justify-center py-2">
          <CircularGauge score={scoreInt} verdict={verdict} />
        </div>

        {/* Score breakdown */}
        <div className="pt-2 border-t border-slate-800 space-y-1">
          <SubLabel>Score Breakdown</SubLabel>
          <ScorePill label="ELA (×0.50)"   value={ela_confidence} color="text-slate-300" />
          <ScorePill label="Noise (×0.30)" value={noise_score}    color="text-slate-300" />
          <ScorePill label="Edge (×0.20)"  value={edge_score}     color="text-slate-300" />
          <div className="flex justify-between pt-1">
            <span className="text-xs text-slate-400 font-semibold">Unified Score</span>
            <span className={`text-sm font-bold ${
              scoreInt >= 60 ? "text-red-400" : scoreInt >= 35 ? "text-amber-400" : "text-emerald-400"
            }`}>
              {scoreInt} / 100
            </span>
          </div>
        </div>

        {/* Verdict callout */}
        <div className={`rounded-xl p-3 text-center ${
          isTampered
            ? "bg-red-950/40 border border-red-800/50"
            : "bg-emerald-950/40 border border-emerald-800/50"
        }`}>
          <p className={`text-xs font-medium ${isTampered ? "text-red-300" : "text-emerald-300"}`}>
            {isTampered
              ? "🚨 Evidence of manipulation detected — image may have been altered."
              : "✅ No significant manipulation signals — image appears authentic."}
          </p>
        </div>
      </Panel>
    </div>

    {/* ── Panel 5 — Copy-Move Detection ───────────────────────────────── */}
    <div className="mt-4 max-w-2xl">
      <Panel title="Copy-Move Analysis" icon="🔁">
        {copy_move?.copy_move_detected ? (
          <>
            <div className="rounded-xl bg-red-950/40 border border-red-800/50 p-3 text-center">
              <p className="text-xs font-medium text-red-300">
                🚨 Copy-move forgery detected — {copy_move.match_count} matching
                keypoint pairs found in different regions.
              </p>
            </div>
            {copy_move.annotated_image_base64 && (
              <>
                <SubLabel>Matched Keypoint Pairs</SubLabel>
                <img
                  src={b64(copy_move.annotated_image_base64)}
                  alt="Copy-move matches"
                  className="w-full rounded-xl object-contain max-h-64 bg-slate-950"
                />
              </>
            )}
          </>
        ) : (
          <div className="rounded-xl bg-emerald-950/40 border border-emerald-800/50 p-3 text-center">
            <p className="text-xs font-medium text-emerald-300">
              ✅ No copy-move patterns found
              {copy_move?.match_count > 0 && (
                <span className="text-slate-500">
                  {" "}({copy_move.match_count} weak matches, below threshold)
                </span>
              )}
            </p>
          </div>
        )}
      </Panel>
    </div>

    {/* ── Download Report ──────────────────────────────────────────────── */}
    {analysis_id && (
      <div className="mt-4 flex justify-center">
        <a
          href={`http://localhost:5005/report/${analysis_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl
                     font-medium text-white bg-gradient-to-r from-violet-600
                     to-blue-600 hover:from-violet-500 hover:to-blue-500
                     transition-all shadow-lg shadow-violet-500/20
                     hover:shadow-violet-500/40"
        >
          📄 Download Report (PDF)
        </a>
      </div>
    )}

    </>
  );
}
