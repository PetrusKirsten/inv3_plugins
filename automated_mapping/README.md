# 🤖 Automated Motor Mapping Plugin for InVesalius Navigator

A fully open-source and automated system for cortical motor mapping using neuronavigation (nTMS), EMG via Arduino, and a collaborative robotic arm.  
Developed as part of a research project at the University of São Paulo (USP) and integrated with the [InVesalius Navigator](https://invesalius.github.io/).

---

## 🧠 Project Overview

This project aims to automate transcranial magnetic stimulation (TMS) motor mapping by integrating:

- Real-time EMG signal acquisition (via microcontroller)
- 3D visualization and neuronavigation (via InVesalius Navigator)
- Precise robotic coil positioning (via cobot)
- Graphical interface for session control and data visualization

Everything is centralized into a single user-friendly plugin running inside InVesalius Navigator.

---

## 🔧 System Components

- 🧲 **TMS Coil** – delivers magnetic pulses
- 💪 **EMG System** – detects muscle response (MEPs)
- 🧠 **InVesalius Navigator** – provides real-time neuroimage guidance
- 🤖 **Collaborative Robot (Cobot)** – positions the TMS coil precisely
- 🧩 **Python Plugin** – synchronizes stimulation, EMG feedback, and robotic trajectory

---

## 🎯 Features

- ✅ Real-time EMG signal acquisition with Arduino + Olimex ECG-EMG module
- ✅ Adjustable signal acquisition rate (from 256 Hz to 1536 Hz)
- ✅ Signal display using PyQtGraph for smooth visualization
- ✅ Serial communication with InVesalius via USB
- ✅ Custom GUI for setup and control
- ✅ Elliptical spiral generation of stimulation points
- ✅ ICP-based surface registration and 3D coordinate correction
- ✅ Automated stimulation triggering + visual feedback

---

## 🖥️ GUI Overview

> ✨ *The plugin GUI includes:*

- Coil trajectory setup (spiral parameters)
- Real-time EMG signal visualization
- Scalp surface + target coordinate display
- Robot control and stimulation feedback loop

📸 **Suggested image:** Screenshot of the plugin GUI showing the spiral points on the 3D scalp + EMG signal plot.

---

## 🌀 Coordinate Mapping Example

The stimulation path is generated using an elliptical spiral projected onto the 3D scalp surface using the **Iterative Closest Point (ICP)** algorithm.

📸 **Suggested image:**  
Side-by-side comparison of:
- Spiral path in 2D  
- Transformed 3D projection on a scalp model

---

## ⚙️ Technologies Used

- **Python** (OOP, threading)
- **PyQt5 / wxPython** – GUI
- **PyQtGraph** – Signal visualization
- **Serial communication (pySerial)**
- **OpenCV + Numpy** – Point transformations
- **Arduino IDE / C++** – EMG signal acquisition
- **Collaborative Robot API** – trajectory execution

---

## 📁 Folder Structure

```bash
automated_mapping/
├── emg.py             # Handles EMG serial interface
├── gui.py             # GUI for trajectory and EMG signal control
├── main.py            # Plugin initialization
├── spiralTMS/         # Spiral trajectory generation and 3D transformation
├── plugin.json        # Plugin config for InVesalius
├── emg-icon.png       # Icon for plugin
└── .idea/             # IDE configs (can be ignored)
