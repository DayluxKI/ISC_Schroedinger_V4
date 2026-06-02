#!/usr/bin/env python3
"""
test_v4_system.py – Automatischer Test der ISC-Schrödinger V4.0 Architektur
Testet GPU-Bridge, Batch-Hashing, und Visualizer ohne Benutzer-Interaktion
Autor: Dmitrij Medkov & DeepSeek-Pupsik
"""

import time
import sys
import numpy as np
import queue
from quantum_core import GPUSchroedingerSack, CPUGPUBridge, N_STATES, DEVICE

def test_gpu_schroedinger_sack():
    """Test: GPUSchroedingerSack mit Batch-Hashing"""
    print("\n" + "=" * 70)
    print("TEST 1: GPUSchroedingerSack – Batch-Evolution & Hashing")
    print("=" * 70)
    
    try:
        sack = GPUSchroedingerSack(n_states=1024, device=DEVICE)
        print(f"✅ GPUSchroedingerSack initialisiert auf {DEVICE}")
        
        # Evolution mit Batch-Hash
        print("\n📊 Starte 5 Evolutions-Schritte...")
        for i in range(5):
            batch_hash = sack.evolve(dt=0.5)
            avg_weight = np.mean(sack.states[:, 0].cpu().numpy())
            avg_dopamine = np.mean(sack.states[:, 1].cpu().numpy())
            avg_cortisol = np.mean(sack.states[:, 2].cpu().numpy())
            print(f"   Schritt {i+1}: W={avg_weight:.3f}, D={avg_dopamine:.3f}, C={avg_cortisol:.3f}")
            print(f"            Batch-Hash: {batch_hash[:20]}...")
        
        # Hash-Kette prüfen
        assert len(sack.hash_chain) == 5, "Hash-Kette sollte 5 Einträge haben"
        print(f"\n✅ Hash-Kette-Länge: {len(sack.hash_chain)} ✓")
        
        # Kollaps testen
        print("\n🎯 Teste Kollaps mit Intent-Vektor...")
        intent = np.array([1.0, 0.0, 0.0])  # Sicherheit
        result = sack.kollabiere(intent)
        
        assert 'winner' in result
        assert 'batch_hash' in result
        assert 'state_hash' in result
        print(f"✅ Kollaps erfolgreich:")
        print(f"   Winner-Index: {result['winner']}")
        print(f"   Winner-Score: {result['score']:.4f}")
        print(f"   Batch-Hash: {result['batch_hash'][:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpugpu_bridge():
    """Test: CPUGPUBridge – Non-Blocking Communication"""
    print("\n" + "=" * 70)
    print("TEST 2: CPUGPUBridge – CPU-GPU Kommunikation")
    print("=" * 70)
    
    try:
        gpu_sack = GPUSchroedingerSack(n_states=1024, device=DEVICE)
        bridge = CPUGPUBridge(gpu_sack)
        print(f"✅ CPUGPUBridge initialisiert")
        
        # Starte Superposition
        print("\n🚀 Starte Superposition...")
        bridge.start_superposition(seed=42)
        time.sleep(1)
        
        # Hole Status
        status = bridge.get_status()
        assert status == 'SUPERPOSITION_STARTED', f"Erwarteter Status 'SUPERPOSITION_STARTED', erhalten: {status}"
        print(f"✅ Status: {status}")
        
        # Request Evolution
        print("\n📈 Starte mehrere Evolution-Zyklen...")
        for i in range(3):
            bridge.request_evolution(dt=0.5)
            time.sleep(0.5)
        
        # Hole Visualisierungsframe
        print("\n🎨 Hole Visualisierungsdaten...")
        frame = bridge.get_visualization_frame()
        if frame and frame.get('type') == 'state':
            data = frame['data']
            assert 'weights' in data
            assert 'dopamine' in data
            assert 'cortisol' in data
            print(f"✅ Visualisierungsframe erhalten:")
            print(f"   Weights: {data['weights'][:5]}...")
            print(f"   Dopamine: {data['dopamine'][:5]}...")
            print(f"   Cortisol: {data['cortisol'][:5]}...")
        
        # Request Collapse
        print("\n💥 Teste Kollaps-Anfrage...")
        try:
            result = bridge.request_collapse([0.5, 0.3, 0.2], timeout=5)
            print(f"   Result type: {type(result)}")
            print(f"   Result keys: {result.keys() if hasattr(result, 'keys') else 'N/A'}")
            print(f"   Result content: {result}")
            assert 'winner' in result, f"Expected 'winner' in result, got: {result}"
            print(f"✅ Kollaps-Result: Winner={result['winner']}, Score={result['score']:.4f}")
        except queue.Empty as e:
            print(f"   ❌ Timeout beim Warten auf Kollaps-Result: {e}")
            raise
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
        
        # Stop
        bridge.stop()
        time.sleep(0.5)
        print("\n✅ Bridge sauber beendet")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST 2 FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_perturbation():
    """Test: Intent-Perturbation (Mausinteraktion)"""
    print("\n" + "=" * 70)
    print("TEST 3: Intent-Perturbation – GPU-Zustand modifizieren")
    print("=" * 70)
    
    try:
        sack = GPUSchroedingerSack(n_states=1024, device=DEVICE)
        
        # Baseline
        print("📊 Baseline-Zustand...")
        baseline_w = np.mean(sack.states[:, 0].cpu().numpy())
        baseline_d = np.mean(sack.states[:, 1].cpu().numpy())
        print(f"   Weight: {baseline_w:.4f}, Dopamine: {baseline_d:.4f}")
        
        # Perturbation
        print("\n🎯 Injiziere Intent-Perturbation...")
        intent = np.array([1.0, 0.0, 0.0])
        sack.inject_intent_perturbation(intent, strength=0.1)
        
        perturbed_w = np.mean(sack.states[:, 0].cpu().numpy())
        perturbed_d = np.mean(sack.states[:, 1].cpu().numpy())
        print(f"   Weight: {perturbed_w:.4f}, Dopamine: {perturbed_d:.4f}")
        
        delta_w = abs(perturbed_w - baseline_w)
        print(f"   Änderung: {delta_w:.4f}")
        
        assert delta_w > 0.001, "Intent-Perturbation sollte Zustand verändern"
        print(f"\n✅ Intent-Perturbation wirkt korrekt")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST 3 FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\033[1m" + "=" * 70 + "\033[0m")
    print("\033[1m   ISC-Schrödinger V4.0 – Automatische Systemtests\033[0m")
    print("\033[1m" + "=" * 70 + "\033[0m")
    print(f"\n🖥️  System: {DEVICE.upper()}")
    print(f"🧠 Zustände: {N_STATES}")
    
    results = []
    
    # Test 1
    results.append(("GPUSchroedingerSack", test_gpu_schroedinger_sack()))
    
    # Test 2
    results.append(("CPUGPUBridge", test_cpugpu_bridge()))
    
    # Test 3
    results.append(("Intent-Perturbation", test_intent_perturbation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST-ZUSAMMENFASSUNG")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\nGesamt: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("\n\033[92m🎉 ALLE TESTS BESTANDEN! V4.0 System ist bereit.\033[0m")
        return 0
    else:
        print(f"\n\033[91m⚠️  {total - passed} Test(s) fehlgeschlagen.\033[0m")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Tests unterbrochen.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
