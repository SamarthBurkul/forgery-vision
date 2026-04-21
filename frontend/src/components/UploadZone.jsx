import { useState, useCallback, useRef } from "react";

export default function UploadZone({ onImageSelect, imagePreview }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback(
    (file) => {
      if (file && file.type.startsWith("image/")) {
        onImageSelect(file);
      }
    },
    [onImageSelect]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);
  const onInputChange = (e) => handleFile(e.target.files[0]);

  const handleSampleClick = async (filename) => {
    try {
      const response = await fetch(`http://localhost:5005/static/samples/${filename}`);
      const blob = await response.blob();
      const file = new File([blob], filename, { type: blob.type });
      handleFile(file);
    } catch (err) {
      console.error("Failed to load sample:", err);
    }
  };

  return (
    <div className="space-y-6">
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`
          relative cursor-pointer rounded-2xl border-2 border-dashed
          transition-all duration-300 overflow-hidden
          ${dragging
            ? "border-violet-500 bg-violet-950/20 drop-active"
            : "border-slate-700 hover:border-slate-500 bg-slate-900/60 hover:bg-slate-900/80"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={onInputChange}
        />

        {imagePreview ? (
          /* Preview state */
          <div className="relative group">
            <img
              src={imagePreview}
              alt="Selected image preview"
              className="w-full max-h-72 object-contain p-2"
            />
            <div className="absolute inset-0 flex items-center justify-center
                            bg-slate-950/70 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-sm font-medium text-white bg-slate-800/80
                               px-4 py-2 rounded-lg border border-slate-600">
                Click to change image
              </span>
            </div>
            <div className="absolute top-3 right-3 bg-violet-600/80 text-white
                            text-xs px-2 py-1 rounded-md backdrop-blur-sm">
              ✓ Ready
            </div>
          </div>
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center text-4xl
                             transition-all duration-300 ${
                               dragging
                                 ? "bg-violet-600/30 scale-110"
                                 : "bg-slate-800"
                             }`}>
              {dragging ? "⬇" : "🖼"}
            </div>

            <div>
              <p className="text-slate-200 font-semibold text-lg">
                {dragging ? "Drop it!" : "Drag & drop an image"}
              </p>
              <p className="text-slate-500 text-sm mt-1">
                or click to browse · JPG, PNG, WEBP supported
              </p>
            </div>

            <div className="flex gap-3 text-xs text-slate-600">
              <span className="px-2 py-1 bg-slate-800 rounded-md">ELA Analysis</span>
              <span className="px-2 py-1 bg-slate-800 rounded-md">Noise Map</span>
              <span className="px-2 py-1 bg-slate-800 rounded-md">Edge Consistency</span>
            </div>
          </div>
        )}
      </div>

      {!imagePreview && (
        <div className="mt-8">
          <p className="text-sm text-slate-400 font-medium mb-3 text-center">Or try a sample:</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { file: "authentic.jpg", label: "Authentic photo",   icon: "📸" },
              { file: "tampered.jpg",  label: "Tampered CASIA",    icon: "✂️" },
              { file: "certificate.jpg", label: "Certificate",       icon: "📜" },
            ].map((s) => (
              <button
                key={s.file}
                onClick={(e) => { e.stopPropagation(); handleSampleClick(s.file); }}
                className="flex flex-col items-center p-3 rounded-xl bg-slate-900/50 border border-slate-800
                           hover:bg-slate-800 hover:border-slate-600 transition-all group"
              >
                <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">{s.icon}</div>
                <span className="text-xs text-slate-300 font-medium">{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
