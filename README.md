# Time Trials GUI

Run from the `time_trials` directory:

```
python3 time_trials_gui.py
```

## Buttons

**Start Time Trials** — launches the simulation, score tracker, and robot in sequence. Disappears once everything is running.

**Start/Stop Timer** — publishes to `/score_tracker` to start or stop the competition timer in the score tracker window.

**Reset Robot** — teleports the robot back to its starting position in Gazebo.
