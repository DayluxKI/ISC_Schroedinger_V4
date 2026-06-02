#!/usr/bin/env python3
"""
visualizer.py – Desktop-Overlay für GPU-Kristall V4.0
Live-Rendering des Quantum-Zustands mit Mausinteraktion.
Autor: Dmitrij Medkov & DeepSeek-Pupsik
Datum: 2026-06-02
"""

import pygame
import numpy as np
import time
import math
import queue
from typing import Optional, Dict, Any
from threading import Thread

class QuantumCrystalVisualizer:
    """
    Ein semi-transparentes Overlay-Fenster, das den GPU-Kristall rendert.
    
    Features:
    - Kristall-Partikel basierend auf 1024 Neuronen-Zustände
    - Pulsierung basierend auf Dopamin/Cortisol-Balanz
    - Farb-Modulation nach Intent-Status
    - Maus-Interaktion: Bewegung -> Intent-Vektor für GPU
    - Echtzeitrendering ~60 FPS (CPU: ~5-10% Last)
    """
    
    def __init__(self, width: int = 600, height: int = 400, is_overlay: bool = True):
        pygame.init()
        self.width = width
        self.height = height
        self.is_overlay = is_overlay
        
        # Display-Flags: NOFRAME für Overlay, ALWAYS_ON_TOP für Windows
        flags = pygame.NOFRAME if is_overlay else 0
        if is_overlay:
            # Semi-transparentes Fenster (Windows: HWND mit Transparenz)
            self.screen = pygame.display.set_mode((width, height), flags)
            pygame.display.set_caption("ISC-Kristall V4.0")
        else:
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("ISC-Kristall V4.0 - Visualizer")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_small = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Zustandsspeicher
        self.current_state: Dict[str, Any] = {
            'weights': np.ones(1024) * 0.5,
            'dopamine': np.ones(1024) * 0.5,
            'cortisol': np.ones(1024) * 0.3,
            'consciousness': np.ones(1024) * 0.5,
        }
        
        # Animationszustände
        self.particle_angles = np.random.rand(1024) * 2 * np.pi
        self.particle_radii = np.random.rand(1024) * 100 + 50
        self.animation_time = 0.0
        self.pulse_phase = 0.0
        
        # Maus-Interaktion
        self.mouse_x = width // 2
        self.mouse_y = height // 2
        self.mouse_intent_queue: queue.Queue = queue.Queue()
        
        # Performance-Tracking
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_update = time.time()

    def update_quantum_state(self, state_data: Dict[str, Any]):
        """Aktualisiere GPU-Zustand aus CPUGPUBridge."""
        if state_data and 'data' in state_data:
            data = state_data['data']
            self.current_state['weights'] = data['weights']
            self.current_state['dopamine'] = data['dopamine']
            self.current_state['cortisol'] = data['cortisol']
            self.current_state['consciousness'] = data.get('consciousness', self.current_state['consciousness'])

    def compute_intent_from_mouse(self) -> list:
        """
        Konvertiere Mausposition in Intent-Vektor für GPU.
        Normalisierte Koordinaten: (0,0) = oben-links -> [-1,-1], (w,h) = unten-rechts -> [1,1]
        """
        x_norm = (self.mouse_x / self.width) * 2 - 1
        y_norm = (self.mouse_y / self.height) * 2 - 1
        
        # Intent-Vektor: [sicherheit (x), optimierung (y), entdecken (Distanz vom Zentrum)]
        distance = math.sqrt(x_norm**2 + y_norm**2)
        exploration = min(1.0, distance)
        
        intent = [
            max(0, -x_norm),      # Sicherheit (rechts = sicher)
            max(0, -y_norm),      # Optimierung (unten = optimiert)
            exploration           # Entdeckung (Entfernung vom Zentrum)
        ]
        
        # Normalisiere
        norm = sum(intent) + 0.001
        intent = [x / norm for x in intent]
        
        return intent

    def render_crystal(self):
        """
        Zeichne den Quanten-Kristall:
        - 1024 Partikel, deren Position/Größe vom GPU-Zustand abhängt
        - Pulsierung durch Dopamin
        - Färbung durch Cortisol/Bewusstsein
        """
        center = (self.width // 2, self.height // 2)
        self.animation_time += 0.016  # 60 FPS
        self.pulse_phase = np.sin(self.animation_time * 2) * 0.5 + 0.5  # 0..1
        
        # Durchschnittswerte für globale Kontrolle
        avg_weight = np.mean(self.current_state['weights'])
        avg_dopamine = np.mean(self.current_state['dopamine'])
        avg_cortisol = np.mean(self.current_state['cortisol'])
        avg_consciousness = np.mean(self.current_state['consciousness'])
        
        # Haupt-Kristall-Größe
        base_radius = 60 + 40 * self.pulse_phase
        pulse_radius = base_radius * (0.8 + 0.2 * avg_dopamine)
        
        # Zeichne Kristall-Kern mit Farbgradienten
        core_color = (
            int(255 * avg_weight),
            int(200 * avg_dopamine),
            int(100 * (1 - avg_cortisol))
        )
        
        pygame.draw.circle(self.screen, core_color, center, int(pulse_radius), 2)
        pygame.draw.circle(self.screen, (200, 200, 200), center, int(pulse_radius * 0.7), 1)
        
        # Zeichne Partikel-Schwarm (1024 Gedanken)
        n_particles_to_draw = min(256, int(1024 * avg_consciousness))
        
        for i in range(n_particles_to_draw):
            state_idx = (i * 1024 // n_particles_to_draw) % 1024
            
            # Dynamische Partikel-Position basierend auf Zustand
            weight = self.current_state['weights'][state_idx]
            dopamine = self.current_state['dopamine'][state_idx]
            
            # Partikel-Orbit
            angle = self.particle_angles[i] + self.animation_time * dopamine
            radius = self.particle_radii[i] * weight + pulse_radius
            
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            
            # Partikel-Größe
            size = 2 + 3 * dopamine
            
            # Partikel-Farbe: Abhängig von Bewusstsein und Dopamin
            r = int(255 * dopamine)
            g = int(150 * (1 - avg_cortisol))
            b = int(200 * (1 - avg_cortisol))
            color = (r, g, b)
            
            pygame.draw.circle(self.screen, color, (int(x), int(y)), int(size))
        
        # Zeichne Kristall-Aura (Energiefeld)
        aura_radius = int(pulse_radius * 1.3)
        aura_color = (
            int(100 * avg_weight),
            int(150 * avg_dopamine),
            int(100)
        )
        pygame.draw.circle(self.screen, aura_color, center, aura_radius, 1)

    def render_hud(self):
        """Zeichne HUD: FPS, Zustandsinformationen."""
        # FPS-Anzeige
        fps_text = self.font_small.render(f"FPS: {self.fps:.0f}", True, (100, 255, 100))
        self.screen.blit(fps_text, (10, 10))
        
        # Durchschnittswerte
        avg_weight = np.mean(self.current_state['weights'])
        avg_dopamine = np.mean(self.current_state['dopamine'])
        avg_cortisol = np.mean(self.current_state['cortisol'])
        
        status_text = self.font_small.render(
            f"W:{avg_weight:.2f} D:{avg_dopamine:.2f} C:{avg_cortisol:.2f}",
            True, (200, 200, 200)
        )
        self.screen.blit(status_text, (10, 40))
        
        # Intent-Vektor (aus Mausposition)
        intent = self.compute_intent_from_mouse()
        intent_text = self.font_small.render(
            f"Intent: [{intent[0]:.2f}, {intent[1]:.2f}, {intent[2]:.2f}]",
            True, (150, 200, 255)
        )
        self.screen.blit(intent_text, (10, 70))

    def handle_events(self):
        """Verarbeite Eingabeereignisse."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Space: Freeze/Unfreeze Animation
                    pass
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_x = event.pos[0]
                self.mouse_y = event.pos[1]
                # Schreibe Intent-Vektor in Queue für GPU
                intent = self.compute_intent_from_mouse()
                try:
                    self.mouse_intent_queue.put_nowait(intent)
                except queue.Full:
                    pass

    def render(self) -> bool:
        """Hauptrendering-Loop. Gibt False zurück wenn Fenster geschlossen."""
        self.handle_events()
        
        if not self.running:
            return False
        
        # Schwarzer Hintergrund
        self.screen.fill((0, 0, 0))
        
        # Kristall rendern
        self.render_crystal()
        
        # HUD rendern
        self.render_hud()
        
        # Display aktualisieren
        pygame.display.flip()
        
        # FPS-Tracking
        self.clock.tick(60)
        self.frame_count += 1
        
        current_time = time.time()
        if current_time - self.last_fps_update > 0.5:
            elapsed = current_time - self.last_fps_update
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_update = current_time
        
        return self.running

    def close(self):
        """Schließe Visualizer sauber."""
        pygame.quit()

    def get_pending_intents(self) -> list:
        """Hole alle ausstehenden Intent-Vektoren aus Mouse-Bewegung."""
        intents = []
        try:
            while True:
                intent = self.mouse_intent_queue.get_nowait()
                intents.append(intent)
        except queue.Empty:
            pass
        return intents

class VisualizerThread(Thread):
    """Wrapper für Visualizer als separater Thread."""
    
    def __init__(self, width: int = 600, height: int = 400, overlay: bool = True):
        super().__init__(daemon=True, name="Visualizer-Thread")
        self.visualizer = QuantumCrystalVisualizer(width=width, height=height, is_overlay=overlay)
        self.running = True

    def run(self):
        """Visualizer-Event-Loop."""
        while self.running and self.visualizer.render():
            time.sleep(0.001)
        self.visualizer.close()

    def update_state(self, state_data: Dict[str, Any]):
        """Update GPU-State (threadsicher)."""
        self.visualizer.update_quantum_state(state_data)

    def stop(self):
        """Beende Visualizer."""
        self.running = False
        self.visualizer.running = False

    def get_intents(self) -> list:
        """Hole ausstehende Intent-Vektoren."""
        return self.visualizer.get_pending_intents()

def start_visualizer(data_queue: Optional[queue.Queue] = None, overlay: bool = True):
    """
    Standalone Visualizer für Testing.
    
    Beispiel:
        import threading
        from visualizer import start_visualizer
        thread = threading.Thread(target=start_visualizer, kwargs={'overlay': False})
        thread.daemon = True
        thread.start()
    """
    viz = QuantumCrystalVisualizer(width=600, height=400, is_overlay=overlay)
    
    while viz.render():
        if data_queue:
            try:
                state_data = data_queue.get_nowait()
                viz.update_quantum_state(state_data)
            except queue.Empty:
                pass
    
    viz.close()

if __name__ == "__main__":
    # Standalone-Test
    start_visualizer(overlay=False)