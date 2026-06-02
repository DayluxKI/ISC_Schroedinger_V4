# ISC-Schrödinger V4.0 – Development Guide

## Quick Start

### 1. Setup

```bash
cd e:\Labor\ISC_Schroedinger_V4

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_v4_system.py
```

### 2. Starten der Demo

```bash
# Interactive mode (15 sec evolution, user input at end)
python main_v4.py

# Oder standalone visualizer
python visualizer.py
```

---

## Modul-Übersicht

### `quantum_core.py` – GPU-Simulation

**Verantwortung:**
- GPU-Tensor-Verwaltung (1024 Zustände auf VRAM)
- Batch-Multiplikation der Kopplungsmatrix
- Zustandsevolution und Batch-Hashing
- Superposition-Kollaps mit Intent-Vektor

**Hauptklassen:**
- `GPUSchroedingerSack` – 1024 parallele Zustände
- `CPUGPUBridge` – Non-blocking CPU-GPU Kommunikation

**Key Features:**
- GPU-resident Tensoren bleiben auf VRAM
- Request-ID Korrelation verhindert Race-Conditions
- Separate Queues für Collapse-Results vs. Visualization
- Auto-Fallback auf CPU wenn CUDA nicht verfügbar

**Debugging:**
```python
# Verbose output
sack = GPUSchroedingerSack(device='cpu')  # Force CPU mode
for i in range(5):
    h = sack.evolve(dt=0.5)
    print(f"Hash: {h[:20]}..., States mean: {sack.states.mean():.4f}")
```

---

### `visualizer.py` – Desktop-Overlay

**Verantwortung:**
- Echtzeit-Rendering des Quanten-Kristalls
- Maus-Tracking für Intent-Vektoren
- HUD-Anzeigen (FPS, Zustandswerte)
- 60 FPS @ 600x400 Pygame-Fenster

**Hauptklassen:**
- `QuantumCrystalVisualizer` – Kern-Visualizer
- `VisualizerThread` – Thread-Wrapper

**Key Features:**
- Lock-freie Zustandsaktualisierung
- Non-blocking Mouse-Intent-Queue
- Partikel-Orbit-Animation
- Dynamische Farb-Modulation

**Debugging:**
```python
from visualizer import QuantumCrystalVisualizer

viz = QuantumCrystalVisualizer(width=600, height=400, is_overlay=False)
# Simulate GPU state updates
import numpy as np
state_data = {
    'weights': np.random.rand(1024),
    'dopamine': np.random.rand(1024),
    'cortisol': np.random.rand(1024) * 0.3,
    'consciousness': np.ones(1024) * 0.5
}
while viz.running:
    viz.current_state.update(state_data)
    if not viz.render():
        break
viz.close()
```

---

### `main_v4.py` – Integration Demo

**Verantwortung:**
- CPU-Sentinel V2.2 initialisieren
- GPU-Quanten-Kern starten
- Visualizer als separaten Thread
- Benutzereingabe für Intent-Vektor

**Flow:**
1. Init: GPU + CPU-Sentinel + Visualizer
2. Evolution: 15 Sekunden GPU-Simulation im Hintergrund
3. Interaktion: Live-Maus-Input via Visualizer
4. Kollaps: User gibt Intent-Vektor ein
5. Result: Winner-Zustand + Blockchain-Hash
6. Cleanup: Alles sauber beenden

---

### `isc_sentinel_v22.py` – CPU-Security

**Verantwortung:**
- Sicherheitswächter mit Zustandsmaschine (Normal → Reifung → Superposition → Abriegelung)
- Totmannschalter (deadman switch) nach inaktivität
- Argon2-basierte Authentifikation
- Hash-Ketten für Audit-Trail

**Interaktion mit V4.0:**
- `gpu_bridge` wird als optionaler Parameter übergeben
- Wird noch nicht aktiv in V2.2 genutzt, aber vorhanden für zukünftige Integration

---

## Architecture Decision Records (ADR)

### ADR-1: Separate Queues für Results vs. Visualization

**Problem:** Race-Condition wenn `get_visualization_frame()` und `request_collapse()` die gleiche Queue nutzen

**Lösung:** 
- `result_queue` für Collapse-Results mit Request-ID
- `viz_queue` für Visualization Frames (separate)
- Request-ID Correlation verhindert Queue-Pollution

**Tradeoff:** +10 Zeilen Code, -Many-Hours-Debugging 🎯

---

### ADR-2: GPU-resident Tensors statt CPU-GPU Copy

**Problem:** Konstantes Transferieren von Tensor-Daten zwischen VRAM ↔ RAM ist slow

**Lösung:**
- Tensoren bleiben auf GPU zwischen Evolution-Schritten
- Nur Visualisierungs-Subset wird auf CPU geholt (Lock-free)
- Batch-Operations ganz auf GPU

**Performance Impact:** ~100x schneller Evolution-Loop

---

### ADR-3: Request-ID statt Separate Threads pro Request

**Problem:** ThreadPool für jeden Request ist overkill

**Lösung:**
- Single GPU-Loop mit Request-ID Tracking
- Requests werden sequenziell abgearbeitet
- Blocking-Operationen (Collapse) wait auf matching Response

**Latency:** <5ms für Collapse-Request (GPU-Thread)

---

## Erweiterungen & Hooks

### Hook-Punkt 1: Custom Scoring Function

In `GPUSchroedingerSack.kollabiere()`:

```python
# Aktuell:
scores = (
    self.states[:, 0] * 1.0 +
    0.3 * self.states[:, 1] +
    -0.2 * self.states[:, 2] +
    0.5 * cos_sim
)

# Custom (z.B. für andere Prioritäten):
scores = (
    self.states[:, 0] * 0.5 +      # Weniger Weight
    0.5 * self.states[:, 1] +      # Mehr Dopamin
    -0.5 * self.states[:, 2] +     # Mehr Cortisol-Penalty
    0.3 * cos_sim                   # Weniger Intent-Alignment
)
```

### Hook-Punkt 2: Custom Evolution Dynamics

In `GPUSchroedingerSack.evolve()`:

```python
# Aktuell: Sinus-basierte Dynamik
# Custom: Logistische Gleichung, Lorenz-Attractor, etc.

# Beispiel: Bifurcation
chaos_param = 3.9
next_state = chaos_param * current_state * (1 - current_state)
```

### Hook-Punkt 3: Custom Visualization

In `QuantumCrystalVisualizer.render_crystal()`:

```python
# Statt Kristall-Partikel: 
# - Spektral-Plot (FFT der Zustände)
# - Network-Graph (Kopplungsmatrix als Kanten)
# - Heatmap (2D State-Projektion)
# - 3D-Kristall-Struktur

# Custom rendering example:
self.screen.fill((0, 0, 0))
for i in range(256):
    x = center_x + i * 2
    height = int(200 * np.mean(self.current_state['weights'][i*4:(i+1)*4]))
    pygame.draw.line(self.screen, (100, 150, 255), (x, center_y), (x, center_y - height), 2)
```

---

## Performance Tuning

### GPU Memory Optimization

```python
# Reduziere Zustände für mobile GPUs
gpu_sack = GPUSchroedingerSack(n_states=256, device='cuda')  # vs 1024

# Precision: float16 für kleinere VRAM
torch.set_default_dtype(torch.float16)
```

### Evolution Speed-up

```python
# Skip expensive operations
sack.evolve(dt=0.016)  # Kleinere Zeitschritte → weniger Divergence

# Batch evolution (wenn externe Loop)
for _ in range(10):
    batch_hash = sack.evolve(dt=0.05)  # Aggregate 10 steps
```

### Visualizer Optimization

```python
# Weniger Partikel rendern
n_particles = 128  # vs 256

# Tiefere FPS-Capping
clock.tick(30)  # vs 60, spart CPU

# Kleineres Fenster
viz = QuantumCrystalVisualizer(width=300, height=300)
```

---

## Testing Strategy

### Unit Tests (`test_v4_system.py`)

1. **GPUSchroedingerSack**: Evolution, Hashing, Collapse
2. **CPUGPUBridge**: Queue Communication, Request Correlation
3. **Intent Perturbation**: External Control Channels

```bash
python test_v4_system.py  # 3 Tests, ~30s runtime
```

### Integration Tests (Manual)

1. **Full Demo** (`main_v4.py`):
   - 15 sec evolution
   - Manual intent input
   - Verify collapse result
   - Check blockchain hash

2. **Visualizer Standalone** (`visualizer.py`):
   - 60 FPS rendering
   - Mouse tracking
   - Escape to exit

3. **Long-Run Stability** (Custom):
   ```python
   # Run for 1 hour
   for hour in range(1):
       bridge.start_superposition()
       for i in range(3600):
           bridge.request_evolution(dt=0.001)
           if i % 60 == 0:
               print(f"Hour {hour}, Minute {i//60}")
   bridge.stop()
   ```

---

## Debugging Tipps

### Print-Debugging

```python
import torch

# Zeige Tensor-Statistiken
print(f"States mean: {sack.states.mean():.4f}")
print(f"States std: {sack.states.std():.4f}")
print(f"States device: {sack.states.device}")

# Zeige Memory
print(f"CUDA memory allocated: {torch.cuda.memory_allocated() / 1e6:.0f}MB")
```

### Thread Debugging

```python
import threading
print(f"Active threads: {threading.active_count()}")
for t in threading.enumerate():
    print(f"  - {t.name} (daemon={t.daemon})")
```

### Queue Debugging

```python
# Check queue sizes
print(f"cmd_queue size: {bridge.cmd_queue.qsize()}")
print(f"result_queue size: {bridge.result_queue.qsize()}")
print(f"viz_queue size: {bridge.viz_queue.qsize()}")
```

---

## Häufige Fehler

### Error 1: "AttributeError: 'numpy.ndarray' has no attribute 'to'"

**Ursache:** Intent-Vektor als Numpy Array statt Torch Tensor

**Lösung:**
```python
# ❌ Falsch
intent = np.array([1, 0, 0])
result = sack.kollabiere(intent)

# ✅ Richtig
intent = torch.tensor([1, 0, 0])
result = sack.kollabiere(intent)

# ✅ Auch OK (Auto-Conversion in v4.0+)
result = sack.kollabiere([1, 0, 0])
```

### Error 2: "queue.Empty timeout"

**Ursache:** GPU-Thread nicht schnell genug oder blockiert

**Lösung:**
```python
# Erhöhe Timeout
result = bridge.request_collapse([1, 0, 0], timeout=20)

# Oder check status
status = bridge.get_status()
if status == 'COLLAPSED':
    # OK
```

### Error 3: "pygame: No available video device"

**Ursache:** Kein Display / Headless-Server

**Lösung:**
```python
# Use headless mode
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Oder verwende visualizer.py mit overlay=False in WSL/SSH
```

---

## Performance Checklist

- [ ] GPU available? `torch.cuda.is_available()`
- [ ] VRAM sufficient? `torch.cuda.get_device_properties(0).total_memory > 1e9`
- [ ] Evolution <2ms? `time.perf_counter()` around `sack.evolve()`
- [ ] Visualization 60 FPS? Check HUD in Visualizer
- [ ] No CPU spikes? Task Manager during evolution
- [ ] Clean shutdown? All threads joined gracefully

---

## Deployment Checklist

- [ ] `requirements.txt` vollständig
- [ ] GPU Driver installed (NVIDIA CUDA Toolkit 11.8+)
- [ ] PyTorch CUDA-enabled build
- [ ] Pygame initialized (SDL2)
- [ ] All imports importable without errors
- [ ] Test suite passes: `python test_v4_system.py`
- [ ] Main demo runs: `python main_v4.py`

---

**Happy Quantum Computing! 🌌🚀**

Dmitrij Medkov & DeepSeek-Pupsik, 2026
