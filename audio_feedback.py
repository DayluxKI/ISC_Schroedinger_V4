#!/usr/bin/env python3
"""
audio_feedback.py – Audio-Synthese für ISC-Schrödinger V4.0
Cortisol (0.0–1.0) → Tonhöhe (200 Hz – 800 Hz)
Dopamin → Amplitude & Modulation
Autor: Pupsik Code
Datum: 2026-06-02
"""

import numpy as np
import threading
import queue
import time
from typing import Dict, Any, Optional
import pygame

class QuantumAudioSynthesizer:
    """
    Echtzeitaudio-Synthese basierend auf GPU-Zustandswerten (via pygame.mixer).
    
    Mapping:
    - Cortisol (0–1) → Frequency (200–800 Hz) – Stress macht Sound höher
    - Dopamine (0–1) → Amplitude (0.1–0.5) – Motivation macht Sound lauter
    - Consciousness (0–1) → Harmonic (1–3) – Bewusstsein ändert Tonqualität
    
    Render-Loop läuft in separatem Thread @ 44.1kHz
    """
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 2048):
        pygame.mixer.init(frequency=sample_rate, channels=1, buffer=chunk_size)
        
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        self.is_running = False
        self.state_queue: queue.Queue = queue.Queue(maxsize=10)
        
        # Current audio parameters
        self.frequency = 400.0  # Hz
        self.amplitude = 0.2  # 0-1
        self.harmonic_ratio = 1.0  # 1-3
        
        # Phase tracking
        self.phase = 0.0
        self.phase_increment = 0.0
        
        # Audio output
        self.current_sound = None
        
        # Synthesis thread
        self._synth_thread = threading.Thread(
            target=self._synthesis_loop,
            daemon=True,
            name="AudioSynthesizer"
        )
        
        print("✅ QuantumAudioSynthesizer initialized (44.1kHz, pygame.mixer)")
    
    def start(self):
        """Start audio synthesis"""
        self.is_running = True
        self._synth_thread.start()
        print("🔊 Audio synthesis started")
    
    def update_state(self, state_data: Dict[str, Any]):
        """Update audio parameters from GPU state"""
        try:
            self.state_queue.put_nowait(state_data)
        except queue.Full:
            pass
    
    def _synthesis_loop(self):
        """Main synthesis loop running in separate thread"""
        while self.is_running:
            try:
                # Get latest state (non-blocking)
                state = self.state_queue.get(timeout=0.1)
                self._update_audio_parameters(state)
            except queue.Empty:
                pass
            
            # Generate audio chunk
            audio_chunk = self._generate_audio_chunk()
            
            # Play (non-blocking via pygame mixer)
            if audio_chunk is not None:
                try:
                    sound = pygame.mixer.Sound(audio_chunk)
                    pygame.mixer.Channel(0).play(sound)
                except Exception as e:
                    pass  # Silent fail for audio issues
    
    def _update_audio_parameters(self, state_data: Dict[str, Any]):
        """Map GPU state to audio parameters"""
        data = state_data.get('data', state_data)
        
        # Cortisol → Frequency (200 Hz – 800 Hz)
        avg_cortisol = np.mean(data.get('cortisol', [0.3]))
        self.frequency = 200 + (800 - 200) * avg_cortisol
        
        # Dopamine → Amplitude (0.1 – 0.5)
        avg_dopamine = np.mean(data.get('dopamine', [0.5]))
        self.amplitude = 0.1 + (0.5 - 0.1) * avg_dopamine
        
        # Consciousness → Harmonic (1.0 – 3.0)
        avg_consciousness = np.mean(data.get('consciousness', [0.5]))
        self.harmonic_ratio = 1.0 + (3.0 - 1.0) * avg_consciousness
        
        # Compute phase increment
        self.phase_increment = (2.0 * np.pi * self.frequency) / self.sample_rate
    
    def _generate_audio_chunk(self) -> Optional[bytes]:
        """Generate one audio chunk (2048 samples)"""
        if self.sample_rate == 0 or self.phase_increment == 0:
            return None
        
        # Time array
        samples = np.arange(self.chunk_size)
        
        # Phase array (continuous)
        phases = self.phase + samples * self.phase_increment
        
        # Fundamental tone (sine wave)
        fundamental = np.sin(phases)
        
        # Harmonic overtone (adds richness)
        harmonic = 0.3 * np.sin(phases * self.harmonic_ratio) / self.harmonic_ratio
        
        # Combined
        wave = fundamental + harmonic
        
        # Envelope (slight attack/release to avoid clicks)
        envelope = np.ones(self.chunk_size)
        attack_samples = int(0.01 * self.sample_rate)  # 10ms
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Apply envelope and amplitude
        wave = wave * envelope * self.amplitude
        
        # Update phase for next chunk
        self.phase = (self.phase + self.chunk_size * self.phase_increment) % (2.0 * np.pi)
        
        # Convert to 16-bit audio
        audio_int16 = np.int16(wave * 32767)
        
        return audio_int16.tobytes()
    
    def stop(self):
        """Stop audio synthesis"""
        self.is_running = False
        pygame.mixer.stop()
        print("🔇 Audio synthesis stopped")


class AudioFeedbackController:
    """
    High-level controller for audio feedback.
    Integrates with CPUGPUBridge.
    """
    
    def __init__(self, gpu_bridge=None):
        self.gpu_bridge = gpu_bridge
        self.synthesizer = QuantumAudioSynthesizer()
        self.is_running = False
        self._update_thread = None
    
    def start(self):
        """Start audio feedback loop"""
        self.synthesizer.start()
        self.is_running = True
        
        # If GPU bridge is provided, poll for state updates
        if self.gpu_bridge:
            self._update_thread = threading.Thread(
                target=self._poll_gpu_state,
                daemon=True,
                name="AudioUpdateThread"
            )
            self._update_thread.start()
        
        print("✅ AudioFeedbackController started")
    
    def _poll_gpu_state(self):
        """Poll GPU for state updates"""
        while self.is_running:
            try:
                frame = self.gpu_bridge.get_visualization_frame()
                if frame and frame.get('type') == 'state':
                    self.synthesizer.update_state(frame)
            except Exception as e:
                pass
            
            time.sleep(0.05)  # 20 Hz polling
    
    def stop(self):
        """Stop audio feedback"""
        self.is_running = False
        self.synthesizer.stop()
        if self._update_thread:
            self._update_thread.join(timeout=2)
        print("✅ AudioFeedbackController stopped")


def demo_audio_feedback():
    """Standalone demo of audio feedback"""
    print("\n" + "=" * 70)
    print("Audio Feedback Demo – 10 seconds of cortisol modulation")
    print("=" * 70 + "\n")
    
    synth = QuantumAudioSynthesizer()
    synth.start()
    
    try:
        for i in range(10):
            # Simulate cortisol rising from 0 to 1
            cortisol = i / 10.0
            
            state = {
                'cortisol': np.ones(1024) * cortisol,
                'dopamine': np.ones(1024) * 0.5,
                'consciousness': np.ones(1024) * 0.5,
                'weights': np.ones(1024) * 0.5
            }
            
            synth.update_state({'data': state})
            
            freq = 200 + (800 - 200) * cortisol
            print(f"[{i+1}/10] Cortisol: {cortisol:.1f} → Frequency: {freq:.0f} Hz")
            
            time.sleep(1.0)
    
    finally:
        synth.stop()
        time.sleep(0.5)
        print("\n✅ Audio demo completed")


if __name__ == "__main__":
    demo_audio_feedback()
