# Simulation-Only Boundary

Intent Fabric does not execute real runtime actions.

Simulation executor behavior:

- `allow` -> simulated success
- `requires_approval` -> pending approval (no execution)
- `deny` -> denied (no execution)

No external side effects are produced by simulation.

Implementation:

`intent_fabric.simulation.executor.SimulationExecutor`
