#!/usr/bin/env python3
"""
overlay_desktop.py – Frameless Desktop-Overlay für ISC-Schrödinger V4.0
Rendert GPU-Kristall in echtem Overlay (nicht pygame, sondern PyQt5)
Autor: Pupsik Code
Datum: 2026-06-02
"""

import sys
import numpy as np
import time
import threading
import queue
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import pyqtSignal, QObject

class StateUpdater(QObject):
    """Signal emitter für Thread-safe State Updates"""
    state_updated = pyqtSignal(dict)

class QuantumOverlay(QMainWindow):
    """
    Echter Desktop-Overlay mit PyQt5:
    - Frameless Window (kein Rahmen)
    - Always-on-Top
    - Transparent background
    - 60 FPS Rendering
    - ~5% CPU Load
    """
    
    def __init__(self, width=600, height=400):
        super().__init__()
        
        self.width = width
        self.height = height
        self.current_state = {
            'weights': np.ones(1024) * 0.5,
            'dopamine': np.ones(1024) * 0.5,
            'cortisol': np.ones(1024) * 0.3,
            'consciousness': np.ones(1024) * 0.5,
        }
        
        # Animation state
        self.animation_time = 0.0
        self.pulse_phase = 0.0
        self.particle_angles = np.random.rand(1024) * 2 * np.pi
        self.particle_radii = np.random.rand(1024) * 100 + 50
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_update = time.time()
        
        # Alpha modulation (transparency)
        self.current_alpha = 200  # 0-255
        self.target_alpha = 200
        self.inactivity_timer = 0.0
        self.inactivity_threshold = 3.0  # seconds
        self.last_mouse_move = time.time()
        
        # Setup Window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Position & Size
        self.setGeometry(100, 100, width, height)
        self.setWindowTitle("ISC-Kristall V4.0")
        
        # Central Widget
        widget = QWidget()
        self.setCentralWidget(widget)
        
        # Timer für 60 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        # State Update Queue
        self.state_queue = queue.Queue(maxsize=5)
        self.last_intent = [0.5, 0.5, 0.5]
        
        print("✅ QuantumOverlay initialized (frameless, always-on-top)")
    
    def update_state(self, state_data):
        """Thread-safe state update"""
        try:
            self.state_queue.put_nowait(state_data)
        except queue.Full:
            pass
    
    def paintEvent(self, event):
        """Render the quantum crystal"""
        # Update state from queue
        try:
            while True:
                state = self.state_queue.get_nowait()
                self.current_state.update(state)
        except queue.Empty:
            pass
        
        # Update alpha based on inactivity
        elapsed_since_mouse = time.time() - self.last_mouse_move
        if elapsed_since_mouse > self.inactivity_threshold:
            self.target_alpha = 80  # Fade to ~30% opacity
        else:
            self.target_alpha = 200  # Full opacity ~80%
        
        # Smooth alpha transition
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(self.current_alpha + 5, self.target_alpha)
        elif self.current_alpha > self.target_alpha:
            self.current_alpha = max(self.current_alpha - 5, self.target_alpha)
        
        # Render
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background (transparent)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Set global alpha for all drawing
        painter.setOpacity(self.current_alpha / 255.0)
        
        # Render crystal
        self._render_crystal(painter)
        
        # Render HUD
        self._render_hud(painter)
        
        painter.end()
        
        # FPS tracking
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_update > 0.5:
            elapsed = current_time - self.last_fps_update
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def _render_crystal(self, painter):
        """Draw the pulsing quantum crystal"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        self.animation_time += 0.016
        self.pulse_phase = np.sin(self.animation_time * 2) * 0.5 + 0.5
        
        # Average values
        avg_weight = np.mean(self.current_state['weights'])
        avg_dopamine = np.mean(self.current_state['dopamine'])
        avg_cortisol = np.mean(self.current_state['cortisol'])
        avg_consciousness = np.mean(self.current_state['consciousness'])
        
        # Crystal core size
        base_radius = 60 + 40 * self.pulse_phase
        pulse_radius = base_radius * (0.8 + 0.2 * avg_dopamine)
        
        # Core color
        r = int(255 * avg_weight)
        g = int(200 * avg_dopamine)
        b = int(100 * (1 - avg_cortisol))
        core_color = QColor(r, g, b)
        
        # Draw core circle
        pen = QPen(core_color, 2)
        painter.setPen(pen)
        painter.drawEllipse(
            int(center_x - pulse_radius),
            int(center_y - pulse_radius),
            int(pulse_radius * 2),
            int(pulse_radius * 2)
        )
        
        # Draw inner circle
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        painter.drawEllipse(
            int(center_x - pulse_radius * 0.7),
            int(center_y - pulse_radius * 0.7),
            int(pulse_radius * 1.4),
            int(pulse_radius * 1.4)
        )
        
        # Draw particle swarm
        n_particles = min(256, int(1024 * avg_consciousness))
        brush = QBrush()
        
        for i in range(n_particles):
            state_idx = (i * 1024 // n_particles) % 1024
            
            weight = self.current_state['weights'][state_idx]
            dopamine = self.current_state['dopamine'][state_idx]
            
            angle = self.particle_angles[i] + self.animation_time * dopamine
            radius = self.particle_radii[i] * weight + pulse_radius
            
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            
            size = 2 + 3 * dopamine
            
            r = int(255 * dopamine)
            g = int(150 * (1 - avg_cortisol))
            b = int(200 * (1 - avg_cortisol))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(r, g, b))
            painter.drawEllipse(int(x - size), int(y - size), int(size * 2), int(size * 2))
        
        # Draw aura
        aura_radius = int(pulse_radius * 1.3)
        pen = QPen(QColor(
            int(100 * avg_weight),
            int(150 * avg_dopamine),
            100
        ), 1)
        painter.setPen(pen)
        painter.drawEllipse(
            int(center_x - aura_radius),
            int(center_y - aura_radius),
            int(aura_radius * 2),
            int(aura_radius * 2)
        )
    
    def _render_hud(self, painter):
        """Draw HUD information"""
        pen = QPen(QColor(100, 255, 100), 1)
        painter.setPen(pen)
        
        font = QFont("Courier", 10)
        painter.setFont(font)
        
        # FPS
        fps_text = f"FPS: {self.fps:.0f}"
        painter.drawText(10, 25, fps_text)
        
        # State values
        avg_weight = np.mean(self.current_state['weights'])
        avg_dopamine = np.mean(self.current_state['dopamine'])
        avg_cortisol = np.mean(self.current_state['cortisol'])
        
        state_text = f"W:{avg_weight:.2f} D:{avg_dopamine:.2f} C:{avg_cortisol:.2f}"
        painter.drawText(10, 50, state_text)
        
        # Intent
        intent_text = f"Intent: [{self.last_intent[0]:.2f}, {self.last_intent[1]:.2f}, {self.last_intent[2]:.2f}]"
        pen = QPen(QColor(150, 200, 255), 1)
        painter.setPen(pen)
        painter.drawText(10, 75, intent_text)
    
    def mouseMoveEvent(self, event):
        """Compute intent from mouse position"""
        x_norm = (event.x() / self.width) * 2 - 1
        y_norm = (event.y() / self.height) * 2 - 1
        
        distance = np.sqrt(x_norm**2 + y_norm**2)
        exploration = min(1.0, distance)
        
        self.last_intent = [
            max(0, -x_norm),
            max(0, -y_norm),
            exploration
        ]
        
        # Normalize
        norm = sum(self.last_intent) + 0.001
        self.last_intent = [x / norm for x in self.last_intent]
    
    def mousePressEvent(self, event):
        """Allow dragging the window"""
        self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Drag window or compute intent"""
        # Update mouse position for inactivity tracking
        self.last_mouse_move = time.time()
        
        if hasattr(self, 'drag_pos') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
        else:
            x_norm = (event.x() / self.width) * 2 - 1
            y_norm = (event.y() / self.height) * 2 - 1
            
            distance = np.sqrt(x_norm**2 + y_norm**2)
            exploration = min(1.0, distance)
            
            self.last_intent = [
                max(0, -x_norm),
                max(0, -y_norm),
                exploration
            ]
            
            norm = sum(self.last_intent) + 0.001
            self.last_intent = [x / norm for x in self.last_intent]
    
    def keyPressEvent(self, event):
        """ESC to close"""
        if event.key() == Qt.Key_Escape:
            self.close()

def start_overlay(state_queue=None):
    """Start the overlay application"""
    app = QApplication(sys.argv)
    overlay = QuantumOverlay(width=600, height=400)
    overlay.show()
    
    # Background state feeder (if queue provided)
    if state_queue:
        def feed_states():
            while overlay.isVisible():
                try:
                    state = state_queue.get(timeout=1.0)
                    overlay.update_state(state)
                except queue.Empty:
                    pass
                time.sleep(0.01)
        
        feeder = threading.Thread(target=feed_states, daemon=True)
        feeder.start()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_overlay()
