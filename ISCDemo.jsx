import { useState, useEffect, useRef, useCallback } from "react";

// ─── Konstanten ──────────────────────────────────────────────────────────────
const N_STATES = 512;
const TICK_MS = 50; // 20 Hz Evolution
const COUPLING_STRENGTH = 0.008;

// ─── Hilfsfunktionen ─────────────────────────────────────────────────────────
function sigmoid(x) { return 1 / (1 + Math.exp(-x)); }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function randn() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// ─── Quanten-Kern (pure JS, simuliert GPU-Logik) ─────────────────────────────
class QuantumCore {
  constructor(n = N_STATES) {
    this.n = n;
    this.weights      = new Float32Array(n).map(() => sigmoid(randn() * 0.01));
    this.dopamine     = new Float32Array(n).map(() => Math.random() * 0.3);
    this.cortisol     = new Float32Array(n).map(() => Math.random() * 0.2);
    this.consciousness= new Float32Array(n).map(() => sigmoid(randn() * 0.01));
    // Sparse Kopplungsmatrix (nur 16 Nachbarn pro State)
    this.coupling = Array.from({ length: n }, () =>
      Array.from({ length: 16 }, () => ({
        idx: Math.floor(Math.random() * n),
        strength: (Math.random() - 0.5) * COUPLING_STRENGTH * 2,
      }))
    );
    this.hashChain = [];
    this.collapsed = false;
    this.collapsedWinner = null;
  }

  evolve(dt = 1.0) {
    const n = this.n;
    const newW = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      let delta = 0;
      for (const { idx, strength } of this.coupling[i]) {
        delta += strength * this.weights[idx];
      }
      newW[i] = sigmoid(this.weights[i] + delta * dt + 0.01 * randn());

      // Dopamin sinkt langsam, steigt gelegentlich
      this.dopamine[i] = clamp(
        this.dopamine[i] - 0.001 * dt + 0.02 * Math.max(0, randn() * 0.3),
        0, 1
      );
      // Cortisol steigt leicht, wird von Dopamin gedämpft
      this.cortisol[i] = clamp(
        this.cortisol[i] + 0.005 * dt - 0.01 * this.dopamine[i] * dt,
        0, 1
      );
      // Bewusstsein driftet langsam
      this.consciousness[i] = sigmoid(
        this.consciousness[i] + 0.001 * randn()
      );
    }
    this.weights = newW;

    // Mini-Hash für Chain (nimmt Summe als Fingerprint)
    const sum = this.weights.reduce((a, b) => a + b, 0);
    const hash = (Math.round(sum * 1e6) % 0xFFFFFF).toString(16).padStart(6, "0");
    this.hashChain.push(hash);
    if (this.hashChain.length > 64) this.hashChain.shift();
    return hash;
  }

  collapse(intentVec) {
    // Score = Aktivation + Dopamin - Cortisol + cosinusähnlichkeit mit Intent
    let bestScore = -Infinity, bestIdx = 0;
    for (let i = 0; i < this.n; i++) {
      const state = [this.weights[i], this.dopamine[i], this.cortisol[i]];
      const dot = intentVec.reduce((s, v, j) => s + v * state[j], 0);
      const magA = Math.sqrt(intentVec.reduce((s, v) => s + v * v, 0)) + 1e-6;
      const magB = Math.sqrt(state.reduce((s, v) => s + v * v, 0)) + 1e-6;
      const cosim = dot / (magA * magB);
      const score = this.weights[i] * 1.0 + 0.3 * this.dopamine[i]
                  - 0.2 * this.cortisol[i] + 0.5 * cosim;
      if (score > bestScore) { bestScore = score; bestIdx = i; }
    }
    this.collapsed = true;
    this.collapsedWinner = bestIdx;
    return {
      winner: bestIdx,
      score: bestScore,
      hash: this.hashChain[this.hashChain.length - 1] ?? "000000",
      winnerState: {
        weight: this.weights[bestIdx],
        dopamine: this.dopamine[bestIdx],
        cortisol: this.cortisol[bestIdx],
        consciousness: this.consciousness[bestIdx],
      }
    };
  }

  getAverages() {
    const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
    return {
      weight: avg(this.weights),
      dopamine: avg(this.dopamine),
      cortisol: avg(this.cortisol),
      consciousness: avg(this.consciousness),
    };
  }
}

// ─── Farb-Helfer ─────────────────────────────────────────────────────────────
function stateToColor(avg) {
  const r = Math.round(80  + 175 * avg.weight);
  const g = Math.round(20  + 180 * avg.dopamine);
  const b = Math.round(200 - 150 * avg.cortisol);
  return `rgb(${r},${g},${b})`;
}

// ─── Partikel-Rendering mit Canvas ───────────────────────────────────────────
function CrystalCanvas({ coreRef, avgRef, intent, frameRef }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);
  const particleAngles = useRef(
    Array.from({ length: 200 }, () => Math.random() * Math.PI * 2)
  );
  const particleRadii = useRef(
    Array.from({ length: 200 }, () => 50 + Math.random() * 110)
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const draw = () => {
      const W = canvas.width, H = canvas.height;
      const cx = W / 2, cy = H / 2;
      timeRef.current += 0.025;
      const t = timeRef.current;

      ctx.clearRect(0, 0, W, H);

      const avg = avgRef.current ?? { weight: 0.5, dopamine: 0.5, cortisol: 0.3, consciousness: 0.5 };
      const pulse = Math.sin(t * 2.1) * 0.5 + 0.5;
      const base = 55 + 35 * pulse;
      const pr = base * (0.8 + 0.22 * avg.dopamine);

      // ── Äußere Aura (mehrere Ringe) ─────────────────────────────────────
      for (let ring = 3; ring >= 1; ring--) {
        const auraR = pr * (1.2 + ring * 0.35);
        const alpha = 0.04 + 0.03 * avg.dopamine - 0.01 * ring;
        const r = Math.round(60 + 140 * avg.weight);
        const g = Math.round(10 + 140 * avg.dopamine);
        const bv = Math.round(180 - 120 * avg.cortisol);
        ctx.beginPath();
        ctx.arc(cx, cy, auraR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r},${g},${bv},${alpha})`;
        ctx.lineWidth = 14 - ring * 3;
        ctx.stroke();
      }

      // ── Partikel-Schwarm ─────────────────────────────────────────────────
      const nP = Math.min(200, Math.round(60 + 140 * avg.consciousness));
      for (let i = 0; i < nP; i++) {
        const si = (i * Math.floor(512 / nP)) % 512;
        const core = coreRef.current;
        const dop = core ? core.dopamine[si] : 0.5;
        const cor = core ? core.cortisol[si] : 0.3;

        particleAngles.current[i] += 0.008 + 0.012 * dop;
        const ang = particleAngles.current[i];
        const rad = particleRadii.current[i] * (core ? core.weights[si] : 0.5) + pr * 0.9;

        const px = cx + rad * Math.cos(ang);
        const py = cy + rad * Math.sin(ang);
        const sz = 1.5 + 2.5 * dop;

        const pr2 = Math.round(255 * dop);
        const pg = Math.round(120 - 100 * cor);
        const pb = Math.round(200 * (1 - cor));
        ctx.beginPath();
        ctx.arc(px, py, sz, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${pr2},${pg},${pb},0.7)`;
        ctx.fill();
      }

      // ── Kristall-Kern ────────────────────────────────────────────────────
      const gr = ctx.createRadialGradient(cx, cy, pr * 0.1, cx, cy, pr);
      const r = Math.round(80 + 170 * avg.weight);
      const g = Math.round(20 + 170 * avg.dopamine);
      const bv = Math.round(200 - 150 * avg.cortisol);
      gr.addColorStop(0, `rgba(${r},${g},${bv},0.95)`);
      gr.addColorStop(0.6, `rgba(${Math.round(r*0.6)},${Math.round(g*0.6)},${Math.round(bv*0.8)},0.5)`);
      gr.addColorStop(1, `rgba(0,0,0,0)`);
      ctx.beginPath();
      ctx.arc(cx, cy, pr, 0, Math.PI * 2);
      ctx.fillStyle = gr;
      ctx.fill();

      // Kern-Rand
      ctx.beginPath();
      ctx.arc(cx, cy, pr, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${r+40},${g+40},${bv+40},0.9)`;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Innerer Ring
      ctx.beginPath();
      ctx.arc(cx, cy, pr * 0.55, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(255,255,255,0.25)`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // ── Winner-Highlight ─────────────────────────────────────────────────
      if (coreRef.current?.collapsed && coreRef.current?.collapsedWinner != null) {
        ctx.beginPath();
        ctx.arc(cx, cy, pr * 1.15, 0, Math.PI * 2);
        const glow = ctx.createRadialGradient(cx, cy, pr * 0.9, cx, cy, pr * 1.4);
        glow.addColorStop(0, "rgba(255,220,80,0.35)");
        glow.addColorStop(1, "rgba(255,180,0,0)");
        ctx.fillStyle = glow;
        ctx.fill();
        ctx.strokeStyle = "rgba(255,220,80,0.7)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // ── Intent-Visualisierung (kleiner Pfeil) ───────────────────────────
      if (intent?.current) {
        const iv = intent.current;
        const ix = (iv[0] - iv[2]) * 40;
        const iy = (iv[1] - iv[2]) * 40;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + ix, cy + iy);
        ctx.strokeStyle = "rgba(100,255,200,0.5)";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + ix, cy + iy, 4, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(100,255,200,0.8)";
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={420}
      height={420}
      style={{ display: "block" }}
    />
  );
}

// ─── Mini-Waveform für Hash-Kette ────────────────────────────────────────────
function HashWave({ chain }) {
  if (!chain || chain.length === 0) return null;
  const h = 32, w = 320;
  const step = w / Math.max(chain.length, 1);
  const points = chain.map((hash, i) => {
    const val = parseInt(hash.slice(0, 2), 16) / 255;
    return `${i * step},${h - val * (h - 4)}`;
  }).join(" ");
  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline points={points} fill="none" stroke="rgba(80,220,160,0.7)" strokeWidth="1.5" />
    </svg>
  );
}

// ─── Bar-Meter ────────────────────────────────────────────────────────────────
function Meter({ label, value, color }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: "#888", letterSpacing: "0.08em", fontFamily: "monospace" }}>
          {label}
        </span>
        <span style={{ fontSize: 11, color, fontFamily: "monospace" }}>
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div style={{
        height: 5, background: "#111", borderRadius: 3,
        overflow: "hidden", border: "1px solid #222"
      }}>
        <div style={{
          height: "100%", width: `${value * 100}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          borderRadius: 3,
          transition: "width 0.3s ease",
          boxShadow: `0 0 6px ${color}66`
        }} />
      </div>
    </div>
  );
}

// ─── Hauptkomponente ─────────────────────────────────────────────────────────
export default function ISCDemo() {
  const coreRef = useRef(null);
  const avgRef  = useRef({ weight: 0.5, dopamine: 0.5, cortisol: 0.3, consciousness: 0.5 });
  const intentRef = useRef([0.33, 0.33, 0.34]);
  const frameRef = useRef(0);

  const [running, setRunning] = useState(false);
  const [avgs, setAvgs] = useState(avgRef.current);
  const [hashChain, setHashChain] = useState([]);
  const [collapseResult, setCollapseResult] = useState(null);
  const [stepCount, setStepCount] = useState(0);
  const [intentMode, setIntentMode] = useState("guardian"); // guardian | optimizer | explorer
  const [log, setLog] = useState([]);
  const tickRef = useRef(null);

  // Core initialisieren
  useEffect(() => {
    coreRef.current = new QuantumCore(N_STATES);
    avgRef.current = coreRef.current.getAverages();
  }, []);

  // Evolution-Loop
  useEffect(() => {
    if (!running) return;
    tickRef.current = setInterval(() => {
      if (!coreRef.current) return;
      coreRef.current.collapsed = false;
      const hash = coreRef.current.evolve(0.8);
      const a = coreRef.current.getAverages();
      avgRef.current = a;
      setAvgs({ ...a });
      setStepCount(s => s + 1);
      setHashChain([...coreRef.current.hashChain]);
    }, TICK_MS);
    return () => clearInterval(tickRef.current);
  }, [running]);

  // Intent-Vektor aus Modus berechnen
  const getIntentVec = useCallback(() => {
    if (intentMode === "guardian")  return [0.8, 0.1, 0.1];
    if (intentMode === "optimizer") return [0.1, 0.8, 0.1];
    return [0.1, 0.2, 0.7]; // explorer
  }, [intentMode]);

  useEffect(() => {
    intentRef.current = getIntentVec();
  }, [intentMode, getIntentVec]);

  const handleCollapse = () => {
    if (!coreRef.current) return;
    const iv = getIntentVec();
    const res = coreRef.current.collapse(iv);
    setCollapseResult(res);
    const ts = new Date().toLocaleTimeString("de-DE");
    const entry = `[${ts}] Kollaps → State #${res.winner} | Score: ${res.score.toFixed(4)} | Hash: ${res.hash}`;
    setLog(l => [entry, ...l.slice(0, 9)]);
  };

  const handleReset = () => {
    setRunning(false);
    clearInterval(tickRef.current);
    coreRef.current = new QuantumCore(N_STATES);
    avgRef.current = coreRef.current.getAverages();
    setAvgs({ ...avgRef.current });
    setHashChain([]);
    setCollapseResult(null);
    setStepCount(0);
    setLog([]);
  };

  const coreColor = stateToColor(avgs);

  const intentLabels = {
    guardian:  { label: "⚔ GUARDIAN",  color: "#4af", desc: "Sicherheit" },
    optimizer: { label: "⚙ OPTIMIZER", color: "#fa4", desc: "Optimierung" },
    explorer:  { label: "✦ EXPLORER",  color: "#a4f", desc: "Exploration" },
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080a0f",
      color: "#c8d8e8",
      fontFamily: "'Courier New', monospace",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "24px 16px 48px",
    }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 28, width: "100%", maxWidth: 860 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.3em", color: "#445", marginBottom: 6 }}>
          ISC-SCHRÖDINGER
        </div>
        <h1 style={{
          fontSize: "clamp(22px,4vw,36px)",
          fontWeight: 700,
          letterSpacing: "0.05em",
          margin: 0,
          background: `linear-gradient(120deg, ${coreColor}, #88ccff, #aaffcc)`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          transition: "background 1s ease"
        }}>
          QUANTUM ORCHESTRATOR V4
        </h1>
        <div style={{ fontSize: 12, color: "#446", marginTop: 6, letterSpacing: "0.15em" }}>
          {N_STATES} PARALLELE ZUSTÄNDE · CPU-SIMULATION
        </div>
      </div>

      <div style={{
        display: "flex", gap: 24, flexWrap: "wrap", justifyContent: "center",
        maxWidth: 900, width: "100%"
      }}>
        {/* Kristall-Canvas */}
        <div style={{
          background: "#0a0e16",
          border: "1px solid #1a2030",
          borderRadius: 16,
          padding: 8,
          boxShadow: `0 0 40px ${coreColor}22`,
          transition: "box-shadow 1s ease",
          flexShrink: 0,
        }}>
          <CrystalCanvas coreRef={coreRef} avgRef={avgRef} intent={intentRef} frameRef={frameRef} />
          {/* Status unter Kristall */}
          <div style={{
            textAlign: "center", paddingTop: 8, fontSize: 10,
            color: "#334", letterSpacing: "0.12em"
          }}>
            {running
              ? <span style={{ color: "#3fa" }}>● SUPERPOSITION AKTIV · Schritt {stepCount}</span>
              : <span style={{ color: "#554" }}>◌ PAUSIERT</span>
            }
          </div>
        </div>

        {/* Rechte Seite – Controls & Metering */}
        <div style={{ flex: 1, minWidth: 240, maxWidth: 360, display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Bio-Metering */}
          <div style={{
            background: "#0a0e16", border: "1px solid #1a2030",
            borderRadius: 12, padding: "16px 18px"
          }}>
            <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#445", marginBottom: 14 }}>
              ◈ BIO-PARAMETER
            </div>
            <Meter label="AKTIVATION  (Weight)"  value={avgs.weight}       color="#58ccff" />
            <Meter label="DOPAMIN     (Motiv.)"   value={avgs.dopamine}     color="#5fdd90" />
            <Meter label="CORTISOL    (Stress)"   value={avgs.cortisol}     color="#ff6060" />
            <Meter label="BEWUSSTSEIN (Meta)"     value={avgs.consciousness} color="#cc88ff" />
          </div>

          {/* Intent-Auswahl */}
          <div style={{
            background: "#0a0e16", border: "1px solid #1a2030",
            borderRadius: 12, padding: "16px 18px"
          }}>
            <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#445", marginBottom: 12 }}>
              ◈ INTENT-VEKTOR
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {Object.entries(intentLabels).map(([key, { label, color }]) => (
                <button key={key} onClick={() => setIntentMode(key)}
                  style={{
                    flex: 1, padding: "7px 4px", fontSize: 9,
                    fontFamily: "monospace", letterSpacing: "0.1em",
                    border: `1px solid ${intentMode === key ? color : "#1a2030"}`,
                    borderRadius: 6, background: intentMode === key ? `${color}22` : "#0d1218",
                    color: intentMode === key ? color : "#445",
                    cursor: "pointer", transition: "all 0.2s",
                    boxShadow: intentMode === key ? `0 0 10px ${color}44` : "none"
                  }}>
                  {label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 10, color: "#445", marginTop: 8, textAlign: "center" }}>
              Aktiv: {intentLabels[intentMode].desc}
              &nbsp;·&nbsp;
              [{getIntentVec().map(v => v.toFixed(1)).join(", ")}]
            </div>
          </div>

          {/* Steuerung */}
          <div style={{
            background: "#0a0e16", border: "1px solid #1a2030",
            borderRadius: 12, padding: "16px 18px", display: "flex", flexDirection: "column", gap: 10
          }}>
            <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#445", marginBottom: 4 }}>
              ◈ STEUERUNG
            </div>
            <button onClick={() => setRunning(r => !r)}
              style={{
                padding: "10px", fontFamily: "monospace", fontSize: 12,
                letterSpacing: "0.15em", border: "none", borderRadius: 8,
                background: running
                  ? "linear-gradient(135deg, #1a3020, #0a2014)"
                  : "linear-gradient(135deg, #102030, #051525)",
                color: running ? "#4fa" : "#58a",
                cursor: "pointer",
                boxShadow: running ? "0 0 16px #4fa4" : "0 0 8px #58a2",
                transition: "all 0.3s",
              }}>
              {running ? "⏸ PAUSE" : "▶ START SUPERPOSITION"}
            </button>

            <button onClick={handleCollapse} disabled={!running && stepCount === 0}
              style={{
                padding: "10px", fontFamily: "monospace", fontSize: 12,
                letterSpacing: "0.15em", border: "1px solid #ffc04488",
                borderRadius: 8,
                background: "linear-gradient(135deg, #201808, #100c04)",
                color: "#ffc044",
                cursor: "pointer",
                boxShadow: "0 0 10px #ffc04422",
                opacity: (!running && stepCount === 0) ? 0.4 : 1,
                transition: "all 0.3s",
              }}>
              ⚡ KOLLAPS AUSLÖSEN
            </button>

            <button onClick={handleReset}
              style={{
                padding: "8px", fontFamily: "monospace", fontSize: 10,
                letterSpacing: "0.12em", border: "1px solid #1a2030",
                borderRadius: 8, background: "transparent",
                color: "#446", cursor: "pointer",
              }}>
              ↺ RESET
            </button>
          </div>

          {/* Kollaps-Ergebnis */}
          {collapseResult && (
            <div style={{
              background: "#0d1208", border: "1px solid #3a5020",
              borderRadius: 12, padding: "14px 16px",
              boxShadow: "0 0 20px #5fa43344"
            }}>
              <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#5a7040", marginBottom: 10 }}>
                ◈ KOLLAPS-ERGEBNIS
              </div>
              <div style={{ fontSize: 11, color: "#8fd060", lineHeight: 1.7 }}>
                <div>Gewinner-State: <strong style={{ color: "#aff070" }}>#{collapseResult.winner}</strong></div>
                <div>Score: <strong style={{ color: "#aff070" }}>{collapseResult.score.toFixed(4)}</strong></div>
                <div>Hash: <span style={{ color: "#5a7040" }}>{collapseResult.hash}</span></div>
                <div>W: {collapseResult.winnerState.weight.toFixed(3)}
                  &nbsp;D: {collapseResult.winnerState.dopamine.toFixed(3)}
                  &nbsp;C: {collapseResult.winnerState.cortisol.toFixed(3)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hash-Kette */}
      <div style={{
        marginTop: 20, background: "#0a0e16", border: "1px solid #1a2030",
        borderRadius: 12, padding: "14px 18px", width: "100%", maxWidth: 860
      }}>
        <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#445", marginBottom: 10 }}>
          ◈ BLOCKCHAIN HASH-KETTE (letzte 64 Blöcke)
        </div>
        <HashWave chain={hashChain} />
        {hashChain.length > 0 && (
          <div style={{ fontSize: 9, color: "#2a3840", marginTop: 6, fontFamily: "monospace" }}>
            {hashChain.slice(-8).join(" · ")}
          </div>
        )}
      </div>

      {/* Protokoll */}
      {log.length > 0 && (
        <div style={{
          marginTop: 16, background: "#080a0a", border: "1px solid #0f2018",
          borderRadius: 12, padding: "14px 18px", width: "100%", maxWidth: 860
        }}>
          <div style={{ fontSize: 10, letterSpacing: "0.25em", color: "#2a4030", marginBottom: 10 }}>
            ◈ KOLLAPS-PROTOKOLL
          </div>
          {log.map((entry, i) => (
            <div key={i} style={{
              fontSize: 10, color: i === 0 ? "#5fa060" : "#2a3830",
              fontFamily: "monospace", lineHeight: 1.8,
              borderLeft: i === 0 ? "2px solid #5fa060" : "2px solid #0f1810",
              paddingLeft: 8, marginBottom: 2,
              transition: "color 0.5s"
            }}>
              {entry}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}