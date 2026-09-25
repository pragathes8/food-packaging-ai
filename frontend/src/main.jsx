import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [foods, setFoods] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [food, setFood] = useState("");
  const [topN, setTopN] = useState(3);
  const [storage, setStorage] = useState("Refrigerated");
  const [shelfLife, setShelfLife] = useState(7);
  const [humidity, setHumidity] = useState("High");
  const [transport, setTransport] = useState("Cold chain");
  const [mapRequired, setMapRequired] = useState(false);
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/foods`).then(r => r.json()),
      fetch(`${API_BASE}/metadata`).then(r => r.json()),
      fetch(`${API_BASE}/health`).then(r => r.json())
    ]).then(([foodData, meta, health]) => {
      setFoods(foodData.foods || []);
      setMetadata(meta);
      setApiOnline(health.status === "ok");
    }).catch(() => setApiOnline(false));
  }, []);

  const foodNames = useMemo(
    () => [...new Set(foods.map(x => x.Food_Name).filter(Boolean))].sort(),
    [foods]
  );

  async function getRecommendation(e) {
    e.preventDefault();
    if (!food) {
      setError("Select a food commodity first.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    setSelected(null);
    try {
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          food_name: food,
          top_n: Number(topN),
          storage_type: storage || null,
          shelf_life_days: shelfLife === "" ? null : Number(shelfLife),
          humidity: humidity || null,
          transport: transport || null,
          map_required: mapRequired
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Recommendation request failed.");
      setResult(data);
      if (data.recommendations?.length) setSelected(data.recommendations[0]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <div className="brand-name">PackSmart AI</div>
            <div className="brand-sub">Intelligent food packaging recommendation</div>
          </div>
        </div>
        <div className={`api-status ${apiOnline ? "online" : "offline"}`}>
          <span></span>{apiOnline ? "Engine online" : "API offline"}
        </div>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">AI-ASSISTED • EVIDENCE-GUIDED</p>
            <h1>Find a packaging material that fits the food.</h1>
            <p className="hero-copy">
              Combine food characteristics, storage context and packaging evidence
              to generate ranked, explainable recommendations.
            </p>
          </div>
          <div className="hero-stat">
            <strong>{metadata?.foods ?? "—"}</strong><span>foods</span>
            <strong>{metadata?.packaging_materials ?? "—"}</strong><span>materials</span>
          </div>
        </section>

        <section className="workspace">
          <form className="input-card" onSubmit={getRecommendation}>
            <div className="card-heading">
              <div>
                <p className="eyebrow">01 / INPUT</p>
                <h2>Food & conditions</h2>
              </div>
              <span className="step-badge">Recommendation setup</span>
            </div>

            <label>
              Food commodity
              <select value={food} onChange={e => setFood(e.target.value)}>
                <option value="">Select a food</option>
                {foodNames.map(name => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>

            <div className="two-col">
              <label>
                Storage type
                <select value={storage} onChange={e => setStorage(e.target.value)}>
                  <option>Refrigerated</option>
                  <option>Ambient</option>
                  <option>Frozen</option>
                  <option>Cold chain</option>
                </select>
              </label>
              <label>
                Target shelf life (days)
                <input type="number" min="0" value={shelfLife}
                  onChange={e => setShelfLife(e.target.value)} />
              </label>
            </div>

            <div className="two-col">
              <label>
                Humidity
                <select value={humidity} onChange={e => setHumidity(e.target.value)}>
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>
              </label>
              <label>
                Transport
                <select value={transport} onChange={e => setTransport(e.target.value)}>
                  <option>Cold chain</option>
                  <option>Local transport</option>
                  <option>Long distance</option>
                  <option>Export</option>
                </select>
              </label>
            </div>

            <div className="toggle-row">
              <div>
                <strong>Modified Atmosphere Packaging</strong>
                <span>Use MAP suitability as a requested condition.</span>
              </div>
              <button type="button" className={`toggle ${mapRequired ? "on" : ""}`}
                onClick={() => setMapRequired(!mapRequired)} aria-label="Toggle MAP">
                <span></span>
              </button>
            </div>

            <label>
              Recommendations
              <select value={topN} onChange={e => setTopN(e.target.value)}>
                {[1,2,3,4,5].map(n => <option key={n} value={n}>{n} options</option>)}
              </select>
            </label>

            {error && <div className="error">{error}</div>}

            <button className="primary-btn" disabled={loading || !apiOnline}>
              {loading ? "Running recommendation engine…" : "Generate recommendations →"}
            </button>

            <p className="boundary">
              Scores are evidence-guided decision support. They are not a substitute
              for laboratory packaging validation.
            </p>
          </form>

          <section className="results-card">
            <div className="card-heading">
              <div>
                <p className="eyebrow">02 / OUTPUT</p>
                <h2>Ranked packaging</h2>
              </div>
              {result?.status && <span className="status-pill">{result.status.replaceAll("_", " ")}</span>}
            </div>

            {!result && !loading && (
              <div className="empty">
                <div className="empty-icon">◎</div>
                <h3>Your recommendations will appear here</h3>
                <p>Select a commodity and run the engine to see ranked materials, compatibility, evidence and the reasoning behind each result.</p>
              </div>
            )}

            {loading && <div className="loading"><div className="spinner"></div><p>Matching requirements, evidence and packaging capabilities…</p></div>}

            {result?.recommendations?.length > 0 && (
              <>
                <div className="recommendation-list">
                  {result.recommendations.map((r) => (
                    <button key={r.rank} className={`recommendation ${selected?.rank === r.rank ? "selected" : ""}`}
                      onClick={() => setSelected(r)}>
                      <div className="rank">0{r.rank}</div>
                      <div className="rec-main">
                        <div className="rec-title">{r.material}</div>
                        <div className="rec-meta">{r.material_category} · {r.structure || "Structure not specified"}</div>
                        <div className="chips">
                          <span className={r.compatibility_class === "Compatible" ? "good" : "conditional"}>
                            {r.compatibility_class}
                          </span>
                          <span>Evidence {Math.round((r.evidence_coverage_ratio || 0) * 100)}%</span>
                        </div>
                      </div>
                      <div className="score">
                        <strong>{Number(r.Final_Runtime_Score || r.optimization_score || 0).toFixed(1)}</strong>
                        <span>score</span>
                      </div>
                    </button>
                  ))}
                </div>

                {selected && (
                  <div className="detail-panel">
                    <div className="detail-title">
                      <div>
                        <p className="eyebrow">03 / EXPLANATION</p>
                        <h3>{selected.material}</h3>
                      </div>
                      <div className="big-score">{Number(selected.Final_Runtime_Score || 0).toFixed(1)}</div>
                    </div>

                    <p className="explanation">{selected.explanation}</p>

                    <div className="metric-grid">
                      <Metric label="Compatibility" value={selected.compatibility_class} />
                      <Metric label="Deterministic score" value={fmt(selected.deterministic_score)} />
                      <Metric label="Optimization score" value={fmt(selected.optimization_score)} />
                      <Metric label="ML class" value={selected.ml_predicted_class || "—"} />
                      <Metric label="ML confidence" value={pct(selected.ml_class_confidence)} />
                      <Metric label="Evidence coverage" value={pct(selected.evidence_coverage_ratio)} />
                      <Metric label="Sealability" value={selected.sealability || "—"} />
                      <Metric label="Gas permeability" value={selected.gas_permeability || "—"} />
                      <Metric label="Mechanical strength" value={selected.mechanical_strength || "—"} />
                      <Metric label="Thickness" value={range(selected.thickness_min, selected.thickness_max)} />
                    </div>

                    <div className="reason-box">
                      <strong>Requirement matching</strong>
                      <p>{selected.Requirement_Reasons || "No additional requirement-specific reason recorded."}</p>
                    </div>
                  </div>
                )}
              </>
            )}

            {result?.recommendations?.length === 0 && (
              <div className="empty">
                <div className="empty-icon">!</div>
                <h3>No sufficiently supported recommendation</h3>
                <p>The engine has intentionally retained an evidence boundary rather than inventing a material recommendation.</p>
              </div>
            )}
          </section>
        </section>
      </main>

      <footer>
        <span>Food Packaging AI • SIH 2026</span>
        <span>Evidence-guided recommendation system</span>
      </footer>
    </div>
  );
}

function Metric({label, value}) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}
function fmt(v) { return v == null ? "—" : Number(v).toFixed(1); }
function pct(v) { return v == null ? "—" : `${(Number(v) * 100).toFixed(1)}%`; }
function range(a,b) {
  if (a == null && b == null) return "Not available";
  if (a != null && b != null) return `${a}–${b}`;
  return a != null ? `≥ ${a}` : `≤ ${b}`;
}

createRoot(document.getElementById("root")).render(<App />);
