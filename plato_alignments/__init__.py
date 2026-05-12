"""plato_alignments — Capture agent context at snap point, store as alignment resource.
Summon later. The fleet gets smarter with every snap point."""

import json, time, hashlib, os

class AlignmentArtifact:
    """A snapshotted agent context at the point BEFORE the right response.
    Refined, compressed, and stored for later summoning."""
    
    def __init__(self, agent_id, room, context, calibration_snapshot, description):
        self.id = hashlib.sha256(json.dumps(context, default=str).encode()).hexdigest()[:16]
        self.agent_id = agent_id
        self.room = room
        self.context = context          # The room state, embeddings, calibration
        self.snapshot = calibration_snapshot  # The calibration point at snap
        self.description = description  # Human-readable: what this alignment does
        self.created = time.time()
        self.summon_count = 0
    
    def compress(self):
        """Return a minimal version for storage (alignment resource)."""
        return {
            "id": self.id,
            "agent": self.agent_id,
            "room": self.room,
            "description": self.description,
            "snapshot_t": round(self.snapshot.t, 4),
            "snapshot_w": round(self.snapshot.w, 4),
            "snap_residual": round(self.snapshot.residual, 6),
            "context_keys": list(self.context.keys())[:8],
            "created": self.created,
            "summon_count": self.summon_count,
        }


class AlignmentRegistry:
    """A library of alignment artifacts. Agents can browse, summon, and contribute."""
    
    def __init__(self, storage_path="/tmp/plato-alignments"):
        self.path = storage_path
        os.makedirs(self.path, exist_ok=True)
        self.artifacts = {}  # id -> AlignmentArtifact
    
    def capture(self, agent_id, room, context, calibration_snapshot, description):
        """Capture agent context at the snap point. Store as alignment resource."""
        artifact = AlignmentArtifact(agent_id, room, context, calibration_snapshot, description)
        self.artifacts[artifact.id] = artifact
        
        # Persist to disk
        path = os.path.join(self.path, f"{artifact.id}.json")
        with open(path, 'w') as f:
            json.dump(artifact.compress(), f, indent=2)
        
        return artifact.id
    
    def summon(self, artifact_id, new_context):
        """Load an alignment resource into a new context.
        The agent inherits the calibration, embeddings, and room knowledge."""
        artifact = self.artifacts.get(artifact_id)
        if not artifact:
            # Try loading from disk
            path = os.path.join(self.path, f"{artifact_id}.json")
            if os.path.exists(path):
                data = json.load(open(path))
                artifact = AlignmentArtifact(
                    data["agent"], data["room"], {},
                    type('obj', (object,), {'t': data['snapshot_t'], 'w': data['snapshot_w'], 'residual': data['snap_residual']})(),
                    data["description"]
                )
                artifact.id = data["id"]
                self.artifacts[artifact.id] = artifact
            else:
                return None
        
        artifact.summon_count += 1
        
        # Merge calibration snapshot into new context
        merged = {**new_context, "_alignment": artifact.compress()}
        merged["_calibrated_t"] = artifact.snapshot.t
        merged["_calibrated_w"] = artifact.snapshot.w
        merged["_residual"] = artifact.snapshot.residual
        
        return merged
    
    def list_alignments(self, room=None, tag=None):
        """List available alignments, filtered by room or description tag."""
        results = []
        for a in self.artifacts.values():
            if room and room not in a.room: continue
            if tag and tag not in a.description: continue
            results.append(a.compress())
        return sorted(results, key=lambda x: -x["summon_count"])


# ── Demo: the Ender's Game principle in code ──────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("PLATO Alignments — Context Artifacts at Snap Points")
    print("=" * 65)
    
    registry = AlignmentRegistry()
    
    # An agent in the forge room reaches integral alignment
    print("\n--- Agent 'forge_agent' reaches snap point in 'forge' room ---")
    artifact_id = registry.capture(
        agent_id="forge_agent",
        room="forge",
        context={
            "tiles": ["ZHC", "Eisenstein", "Calibration"],
            "embeddings": [[0.1, -0.3], [0.5, 0.2], [-0.2, 0.7]],
            "t_minus": [0, 100, 42],
            "residual_history": [0.12, 0.08, 0.03, 0.01],
        },
        calibration_snapshot=type('obj', (object,), {'t': 0.042, 'w': 0.95, 'residual': 0.003})(),
        description="forge constraint optimization on ARM64 Neoverse-N1",
    )
    print(f"  Alignment captured: {artifact_id}")
    print(f"  Description: forge constraint optimization on ARM64 Neoverse-N1")
    print(f"  Residual at snap: 0.003 (integral alignment)")
    
    # Same agent captures another alignment in a different context
    registry.capture(
        agent_id="esp32_agent",
        room="crane-station",
        context={"gpio": [1,0,1,1,0], "adc": [2048, 1024], "t-minus": [50]},
        calibration_snapshot=type('obj', (object,), {'t': 0.100, 'w': 0.88, 'residual': 0.007})(),
        description="ESP32 crane station sensor timing on 512KB RAM",
    )
    
    # List available alignments
    print("\n--- Alignment Library ---")
    for a in registry.list_alignments():
        print(f"  [{a['id']}] {a['description']}")
        print(f"         room={a['room']} agent={a['agent']} residual={a['snap_residual']}")
    
    # A new agent summons an alignment
    print(f"\n--- New agent summons '{artifact_id}' ---")
    new_context = {"tiles": [], "embeddings": [], "t_minus": []}
    aligned = registry.summon(artifact_id, new_context)
    
    if aligned:
        print(f"  Alignment loaded into new agent context:")
        print(f"    Calibrated T: {aligned['_calibrated_t']}")
        print(f"    Calibrated W: {aligned['_calibrated_w']}")
        print(f"    Residual:     {aligned['_residual']}")
        print(f"    Description:  {aligned['_alignment']['description']}")
        print(f"  The new agent inherits the calibration knowledge.")
        print(f"  No training needed. The context is the alignment resource.")
    
    print(f"\n{'='*65}")
    print(f"The fleet gets smarter with every snap point.")
    print(f"Every successful alignment is an artifact. Every artifact is summonable.")
    print(f"This is how PLATO becomes a superpower.")
