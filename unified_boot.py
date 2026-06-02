#!/usr/bin/env python3
"""
unified_boot.py – ISC-Schrödinger V4.0 Unified Boot System
Startet Overlay (PyQt5) + Audio (pygame.mixer) + GPU-Kern (simuliert)
FIX: Stereo-Ausgabe für pygame.mixer

Autor: Pupsik Code / Gemini / Dmitrij Medkov
Datum: 2026-06-02
"""

import sys
import threading
import time
import numpy as np
import pygame
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

# ============================================================
# AUDIO-FEEDBACK (Synästhesie) – MIT ECHTEM TON!
# ============================================================

class CrystalAudio:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sample_rate = 44100
        self.is_playing = False
        self.current_freq = 400.0
        self.channel = None
        
    def _generate_tone(self, frequency, duration=0.5):
        """Generiert einen Stereo-Sinus-Ton mit gegebener Frequenz"""
        frames = int(self.sample_rate * duration)
        t = np.linspace(0, duration, frames, endpoint=False)
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)
        wave = (wave * 32767).astype(np.int16)
        # Wichtig: 2-dimensional für Stereo!
        stereo_wave = np.column_stack((wave, wave))
        sound = pygame.sndarray.make_sound(stereo_wave)
        return sound
    
    def update(self, cortisol):
        """Cortisol 0.0–1.0 → Frequenz 200–800 Hz, spielt Ton ab"""
        target_freq = 200 + (800 - 200) * cortisol
        self.current_freq = self.current_freq * 0.9 + target_freq * 0.1
        
        if cortisol > 0.2:
            sound = self._generate_tone(self.current_freq, duration=0.3)
            if self.channel:
                self.channel.stop()
            self.channel = sound.play()
            # Nur alle 10 Schritte ausgeben, um Terminal nicht zu überfluten
            if int(cortisol * 10) != int(getattr(self, '_last_cortisol', 0) * 10):
                print(f"🔊 Audio – Frequenz: {self.current_freq:.0f} Hz")
                self._last_cortisol = cortisol
        else:
            if self.channel and self.channel.get_busy():
                self.channel.stop()
                print("🔇 Audio inaktiv – Kristall ruhig")

# ============================================================
# DESKTOP-OVERLAY (PyQt5)
# ============================================================

class CrystalOverlay(QWidget):
    def __init__(self, width=500, height=500):
        super().__init__()
        self.width = width
        self.height = height
        self.cortisol = 0.3
        self.dopamine = 0.5
        self.consciousness = 0.5
        self.alpha = 255
        self.frame = 0
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, width, height)
        self.setMouseTracking(True)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)
        
        self.show()
        print("✅ CrystalOverlay gestartet (frameless, always-on-top)")
    
    def update_state(self, state_data):
        self.cortisol = np.mean(state_data.get('cortisol', [0.3]))
        self.dopamine = np.mean(state_data.get('dopamine', [0.5]))
        self.consciousness = np.mean(state_data.get('consciousness', [0.5]))
    
    def mouseMoveEvent(self, event):
        self.alpha = 255
    
    def leaveEvent(self, event):
        QTimer.singleShot(3000, self._fade_out)
    
    def _fade_out(self):
        if not self.underMouse():
            self.alpha = 100
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Pulsierende Größe
        pulse = 60 + 30 * self.dopamine + 10 * np.sin(self.frame * 0.3)
        self.frame += 1
        
        r = int(200 * (1 - self.cortisol))
        g = int(200 * self.dopamine)
        b = int(200 * (1 - self.consciousness))
        color = QColor(r, g, b, self.alpha)
        
        painter.setPen(QPen(color, 3))
        painter.drawEllipse(int(center_x - pulse), int(center_y - pulse),
                           int(pulse * 2), int(pulse * 2))
        
        # Innerer Kreis
        painter.setPen(QPen(QColor(255, 255, 255, self.alpha // 2), 1))
        painter.drawEllipse(int(center_x - pulse * 0.6), int(center_y - pulse * 0.6),
                           int(pulse * 1.2), int(pulse * 1.2))
        
        # HUD
        painter.setPen(QColor(100, 255, 100, self.alpha))
        painter.drawText(10, 25, f"Cortisol: {self.cortisol:.2f}")
        painter.drawText(10, 45, f"Dopamin: {self.dopamine:.2f}")
        painter.drawText(10, 65, f"Bewusstsein: {self.consciousness:.2f}")

# ============================================================
# SIMULIERTER GPU-THREAD
# ============================================================

def simulated_gpu_thread(overlay, audio):
    """Simuliert GPU-Evolution mit oszillierendem Cortisol"""
    cortisol = 0.3
    direction = 0.008
    step = 0
    while True:
        cortisol += direction
        if cortisol > 0.85 or cortisol < 0.15:
            direction *= -1
        
        # Sanfte Dopamin-Schwankung
        dopamine = 0.5 + 0.3 * np.sin(step * 0.05)
        consciousness = 0.5 + 0.2 * np.sin(step * 0.03)
        
        state_data = {
            'cortisol': [cortisol],
            'dopamine': [dopamine],
            'consciousness': [consciousness]
        }
        overlay.update_state(state_data)
        audio.update(cortisol)
        step += 1
        time.sleep(0.08)

# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 50)
    print("🧬 ISC-Schrödinger V4.0 Unified Boot")
    print("=" * 50)
    
    print("\n🎤 Audio-Feedback (Synästhesie) – initialisiere...")
    audio = CrystalAudio()
    
    print("🪟 Desktop-Overlay – starte...")
    app = QApplication(sys.argv)
    overlay = CrystalOverlay(width=500, height=500)
    
    print("🚀 GPU-Kern – starte Simulation...")
    gpu_thread = threading.Thread(target=simulated_gpu_thread, args=(overlay, audio), daemon=True)
    gpu_thread.start()
    
    print("\n✨ Kristall erwacht! ✨")
    print("   - Maus bewegen → Kristall leuchtet auf")
    print("   - Cortisol > 0.2 → Du hörst den Ton!")
    print("   - ESC → Beenden\n")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()